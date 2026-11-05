#!/usr/bin/env python3
"""Fill a local Superdesk e2e instance with a fictional newsroom for documentation screenshots.

Creates roles, users, desks, stages, text articles in several workflow states, pictures, a package,
marks and locks through the Superdesk REST API. The content lives in seed_data.py. Every run is
idempotent: objects are looked up by a stable key (role/desk name, username, item guid) first.

Standard library only (Pillow is used for generated pictures when it is installed). See SEED.md.

    python3 seed.py --api-url http://localhost:5002/api [--user admin --password admin]
                    [--dry-run] [--reset] [--images-dir DIR] [--send-and-duplicate-desk]
                    [--system-message-on]
"""

import argparse
import base64
import datetime
import io
import json
import math
import os
import random
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import seed_data as data  # noqa: E402

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python < 3.9
    ZoneInfo = None

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFilter
except ImportError:
    Image = None

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S+0000"
PUBLISHED_STATES = {"published", "corrected", "killed", "recalled", "unpublished"}
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")
BANNED_WORDS = re.compile(r"\b(test|tests|testing|foo|lorem|ipsum|dummy|fixme)\b", re.IGNORECASE)

# Limits of the `Story` content profile and the `picture` profile in the e2e snapshot.
MAX_SLUGLINE = 24
MAX_HEADLINE = 64
MAX_ABSTRACT = 160


class SeedError(Exception):
    pass


class ApiError(SeedError):
    def __init__(self, method, url, status, body):
        self.method = method
        self.url = url
        self.status = status
        self.body = body
        super().__init__("{} {} -> HTTP {}\n{}".format(method, url, status, body))

    @property
    def message(self):
        try:
            parsed = json.loads(self.body)
        except ValueError:
            return self.body.strip()
        if isinstance(parsed, dict):
            error = parsed.get("_error") or {}
            return parsed.get("_message") or error.get("message") or json.dumps(parsed.get("_issues") or parsed)
        return self.body.strip()


def log(action, kind, name, detail=""):
    print("[{:<8}] {:<9} {}{}".format(action, kind, name, "  " + detail if detail else ""), flush=True)


# ---- HTTP -------------------------------------------------------------------------------------------


class Client:
    """Minimal Superdesk REST client authenticated with one session token."""

    def __init__(self, api_url, token=None, username=None, user_id=None):
        self.api_url = api_url
        self.token = token
        self.username = username
        self.user_id = user_id

    def request(self, method, path, payload=None, params=None, etag=None, body=None, content_type=None):
        url = self.api_url + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = "Basic " + base64.b64encode((self.token + ":").encode()).decode()
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            content_type = "application/json"
        if content_type:
            headers["Content-Type"] = content_type
        if etag:
            headers["If-Match"] = etag
        req = urllib.request.Request(url, data=body, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as err:
            raise ApiError(method, url, err.code, err.read().decode("utf-8", errors="replace"))
        except urllib.error.URLError as err:
            raise SeedError("Cannot reach {}: {}".format(url, err.reason))
        return json.loads(raw.decode("utf-8")) if raw else {}

    def get(self, path, **params):
        return self.request("GET", path, params=params or None)

    def get_optional(self, path, **params):
        try:
            return self.get(path, **params)
        except ApiError as err:
            if err.status == 404:
                return None
            raise

    def find_one(self, path, where, **params):
        params.update({"where": json.dumps(where), "max_results": 1})
        items = self.get(path, **params).get("_items", [])
        return items[0] if items else None

    def find_all(self, path, where, **params):
        params.update({"where": json.dumps(where), "max_results": 200})
        return self.get(path, **params).get("_items", [])

    def post(self, path, payload):
        return self.request("POST", path, payload=payload)

    def patch(self, path, payload, etag):
        return self.request("PATCH", path, payload=payload, etag=etag)

    def delete(self, path, etag):
        return self.request("DELETE", path, etag=etag)

    def post_multipart(self, path, fields, file_field, filename, content, mimetype):
        boundary = "----superdesk-seed-" + uuid.uuid4().hex
        chunks = []
        for name, value in fields.items():
            chunks.append(
                '--{}\r\nContent-Disposition: form-data; name="{}"\r\n\r\n{}\r\n'.format(boundary, name, value).encode(
                    "utf-8"
                )
            )
        chunks.append(
            '--{}\r\nContent-Disposition: form-data; name="{}"; filename="{}"\r\nContent-Type: {}\r\n\r\n'.format(
                boundary, file_field, filename, mimetype
            ).encode("utf-8")
        )
        chunks.append(content)
        chunks.append("\r\n--{}--\r\n".format(boundary).encode("utf-8"))
        return self.request(
            "POST", path, body=b"".join(chunks), content_type="multipart/form-data; boundary=" + boundary
        )


def login(api_url, username, password):
    try:
        res = Client(api_url).post("/auth_db", {"username": username, "password": password})
    except ApiError as err:
        if err.status in (400, 401, 403):
            raise SeedError("Login failed for user {!r}: {}".format(username, err.message))
        raise
    client = Client(api_url, token=res["token"], username=username, user_id=str(res["user"]))
    # The preferences resource is addressed by session id, not user id.
    client.session_id = str(res["_id"])
    return client


# ---- helpers ----------------------------------------------------------------------------------------


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)


def fmt(dt):
    return dt.astimezone(datetime.timezone.utc).strftime(DATE_FORMAT)


def schedule_tz():
    """Named zone for publish schedules, or None when zone data is unavailable (times are then UTC)."""
    if ZoneInfo is None:
        return None
    try:
        return ZoneInfo(data.NEWSROOM["timezone"])
    except Exception:
        return None


def wall_time(spec):
    """Local wall time for a schedule/embargo spec, in the format the client sends.

    Superdesk stores `publish_schedule` and `embargo` as local time with a literal +0000 suffix and keeps
    the zone in `schedule_settings.time_zone` (see IArticle.publish_schedule in superdesk-api.d.ts).
    """
    tz = schedule_tz()
    today = datetime.datetime.now(tz or datetime.timezone.utc).date()
    day = today + datetime.timedelta(days=spec["days"])
    return "{}T{}:00+0000".format(day.isoformat(), spec["time"])


def schedule_settings():
    return {"time_zone": data.NEWSROOM["timezone"] if schedule_tz() else None}


def guid_for(key):
    return data.NEWSROOM["guid_prefix"] + key


def item_path(guid, action=None):
    quoted = urllib.parse.quote(guid, safe=":")
    if action in ("publish", "spike", "unspike"):
        return "/archive/{}/{}".format(action, quoted)
    if action:
        return "/archive/{}/{}".format(quoted, action)
    return "/archive/" + quoted


def subject_list(keys):
    result = []
    for key in keys:
        qcode, name = data.SUBJECTS[key]
        parent = None if qcode.endswith("000000") else qcode[:2] + "000000"
        result.append({"qcode": qcode, "name": name, "parent": parent, "scheme": None})
    return result


def category_list(qcode):
    names = {c["qcode"]: c["name"] for c in data.CATEGORIES}
    return [{"qcode": qcode, "name": names[qcode]}]


def display_name(username, users_by_name):
    spec = users_by_name.get(username)
    return "{} {}".format(spec["first_name"], spec["last_name"]) if spec else username


def all_desks(include_send_and_duplicate):
    desks = list(data.DESKS)
    if include_send_and_duplicate:
        desks.append(data.SEND_AND_DUPLICATE_DESK)
    return desks


# Same word pattern as the client's spell checker (scripts/core/editor3/components/spellchecker).
SPELLCHECK_WORD = re.compile("[0-9a-zA-Z\u00C0-\u1FFF\u2C00-\uD7FF]+")


def seed_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from seed_strings(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from seed_strings(v)


def dictionary_words(system_words=None):
    """Every word used in seed_data.py, plus the system word list when it exists, as a {word: 1} model."""
    words = set()
    for name in dir(data):
        if name.isupper():
            for text in seed_strings(getattr(data, name)):
                words.update(w for w in SPELLCHECK_WORD.findall(text) if not w.isdigit())
    if system_words and os.path.exists(system_words):
        with open(system_words, encoding="utf-8", errors="ignore") as fh:
            words.update(line.strip() for line in fh if line.strip())
    words |= {w.lower() for w in words}
    return {w: 1 for w in sorted(words)}


# ---- data validation (runs before any request, also in --dry-run) -----------------------------------


def validate_data():
    problems = []
    seed_users = {u["username"] for u in data.USERS}
    known_users = seed_users | set(data.SNAPSHOT_USERS)
    roles = {r["name"] for r in data.ROLES}
    desks = {d["name"]: d for d in data.DESKS}
    articles = {a["key"]: a for a in data.ARTICLES}
    keys = [a["key"] for a in data.ARTICLES] + [p["key"] for p in data.PICTURES] + [p["key"] for p in data.PACKAGES]

    for key in {k for k in keys if keys.count(k) > 1}:
        problems.append("duplicate item key {!r}".format(key))

    for user in data.USERS:
        if user["role"] not in roles:
            problems.append("user {}: unknown role {!r}".format(user["username"], user["role"]))
        if user.get("default_desk") and user["default_desk"] not in desks:
            problems.append("user {}: unknown default desk {!r}".format(user["username"], user["default_desk"]))
        if len(user["username"]) < 5:
            problems.append("user {}: password (= username) must be at least 5 characters".format(user["username"]))
        if not re.match(r"^[a-zA-Z0-9]+$", user["sign_off"]):
            problems.append("user {}: sign_off must be letters and digits only".format(user["username"]))

    if data.ADMIN_DEFAULT_DESK and data.ADMIN_DEFAULT_DESK not in desks:
        problems.append("ADMIN_DEFAULT_DESK {!r} is not in DESKS".format(data.ADMIN_DEFAULT_DESK))

    for desk in list(data.DESKS) + [data.SEND_AND_DUPLICATE_DESK]:
        for member in desk.get("members", []):
            if member not in known_users:
                problems.append("desk {}: unknown member {!r}".format(desk["name"], member))
        names = [s["name"] for s in desk["stages"]]
        if len(names) != len(set(names)):
            problems.append("desk {}: duplicate stage names".format(desk["name"]))

    def members_of(desk_name):
        desk = desks[desk_name]
        members = set(desk.get("members", []))
        if desk.get("snapshot"):
            members |= set(data.SNAPSHOT_USERS)  # verified against the server at run time
        return members

    def check_text(label, text, limit=None):
        if limit and len(text) > limit:
            problems.append("{}: {} characters, the profile allows {}".format(label, len(text), limit))
        if BANNED_WORDS.search(text):
            problems.append("{}: contains placeholder wording {!r}".format(label, BANNED_WORDS.search(text).group()))

    def check_placement(label, spec):
        if spec["desk"] not in desks:
            problems.append("{}: unknown desk {!r}".format(label, spec["desk"]))
            return
        if spec["stage"] not in [s["name"] for s in desks[spec["desk"]]["stages"]]:
            problems.append("{}: desk {} has no stage {!r}".format(label, spec["desk"], spec["stage"]))
        if spec["author"] not in known_users:
            problems.append("{}: unknown author {!r}".format(label, spec["author"]))
        elif spec["author"] not in members_of(spec["desk"]):
            problems.append("{}: author {} is not a member of {}".format(label, spec["author"], spec["desk"]))
        check_text(label + " slugline", spec["slugline"], MAX_SLUGLINE)
        check_text(label + " headline", spec["headline"], MAX_HEADLINE)

    categories = {c["qcode"] for c in data.CATEGORIES}
    for art in data.ARTICLES:
        label = "article " + art["key"]
        check_placement(label, art)
        check_text(label + " abstract", art["abstract"], MAX_ABSTRACT)
        for i, para in enumerate(art["body"]):
            check_text("{} paragraph {}".format(label, i + 1), para)
        check_text(label + " ednote", art.get("ednote", ""))
        if art["genre"] not in data.GENRES:
            problems.append("{}: unknown genre {!r}".format(label, art["genre"]))
        if art["category"] not in categories:
            problems.append("{}: unknown category {!r}".format(label, art["category"]))
        for subject in art["subjects"]:
            if subject not in data.SUBJECTS:
                problems.append("{}: unknown subject {!r}".format(label, subject))
        if art["place"] not in data.PLACES:
            problems.append("{}: unknown place {!r}".format(label, art["place"]))
        action = art.get("action")
        if action not in (None, "publish", "schedule", "spike"):
            problems.append("{}: unknown action {!r}".format(label, action))
        if action == "schedule" and not art.get("publish_at"):
            problems.append("{}: action 'schedule' needs publish_at".format(label))
        if art.get("publish_at") and action != "schedule":
            problems.append("{}: publish_at is only used with action 'schedule'".format(label))
        if art.get("embargo") and action not in ("publish", "schedule"):
            problems.append("{}: embargo is only applied when the item is published or scheduled".format(label))
        for field in ("publish_at", "embargo"):
            when = art.get(field)
            if when and not re.match(r"^([01]\d|2[0-3]):[0-5]\d$", when.get("time", "")):
                problems.append("{}: {} time must be HH:MM".format(label, field))
            elif when and when["time"] == "00:00" and field == "embargo":
                problems.append("{}: the server rejects an embargo at exactly 00:00".format(label))
            if when and when.get("days", 0) < 1:
                problems.append("{}: {} must be at least one day ahead, the server refuses past times".format(label, field))
        if art["desk"] == "Sports" and re.search(r"football|basketball", art["slugline"], re.IGNORECASE):
            problems.append("{}: the snapshot product blocks Football/Basketball sluglines".format(label))

    for pic in data.PICTURES:
        label = "picture " + pic["key"]
        check_placement(label, pic)
        check_text(label + " caption", pic["description_text"])

    packaged = set()
    for pkg in data.PACKAGES:
        label = "package " + pkg["key"]
        check_placement(label, pkg)
        check_text(label + " abstract", pkg["abstract"], MAX_ABSTRACT)
        for key in pkg["items"]:
            packaged.add(key)
            if key not in articles:
                problems.append("{}: unknown item {!r}".format(label, key))
            elif articles[key].get("action") in ("schedule", "spike"):
                problems.append("{}: item {} cannot be scheduled or spiked while packaged".format(label, key))

    marked, locked = {}, {}
    for mark in data.MARKS:
        art = articles.get(mark["item"])
        marked[mark["item"]] = mark["user"]
        if art is None:
            problems.append("mark: unknown item {!r}".format(mark["item"]))
        elif art.get("action"):
            problems.append("mark {}: only unpublished items on a stage can be marked".format(mark["item"]))
        if mark["user"] not in known_users:
            problems.append("mark {}: unknown user {!r}".format(mark["item"], mark["user"]))

    for lock in data.LOCKS:
        art = articles.get(lock["item"])
        locked[lock["item"]] = lock["user"]
        if art is None:
            problems.append("lock: unknown item {!r}".format(lock["item"]))
            continue
        if art.get("action"):
            problems.append("lock {}: only unpublished items on a stage can be locked".format(lock["item"]))
        if lock["user"] not in members_of(art["desk"]):
            problems.append("lock {}: {} is not a member of {}".format(lock["item"], lock["user"], art["desk"]))
        if lock["item"] in marked and marked[lock["item"]] != lock["user"]:
            problems.append("lock {}: item is also marked; marking a locked item fails".format(lock["item"]))
        if lock["item"] in packaged:
            problems.append("lock {}: packaged items are left unlocked so the package stays editable".format(lock["item"]))

    for user in data.USERS:
        check_text("user " + user["username"], " ".join([user["first_name"], user["last_name"], user["job_title"]]))

    item_keys = set(keys) | {p["key"] for p in data.PERSONAL_ITEMS}
    for key in [p["key"] for p in data.PERSONAL_ITEMS]:
        if key in keys:
            problems.append("personal item {}: key already used by an article, picture or package".format(key))
    for p in data.PERSONAL_ITEMS:
        check_text("personal item " + p["key"], " ".join([p["slugline"], p["headline"], p["body"]]))
    highlights = {h["name"] for h in data.HIGHLIGHTS}
    for h in data.HIGHLIGHTS:
        for desk in h["desks"]:
            if desk not in desks:
                problems.append("highlight {}: unknown desk {!r}".format(h["name"], desk))
    for key, names in data.HIGHLIGHT_MARKS.items():
        if key not in articles:
            problems.append("highlight mark: unknown item {!r}".format(key))
        for name in names:
            if name not in highlights:
                problems.append("highlight mark {}: unknown highlight {!r}".format(key, name))
    lists = {c["name"] for c in data.CONTENT_LISTS}
    for c in data.CONTENT_LISTS:
        for key in c["items"] + ([c["pinned"]] if c.get("pinned") else []):
            if key not in articles:
                problems.append("content list {}: unknown item {!r}".format(c["name"], key))
            elif articles[key].get("action") == "spike":
                problems.append("content list {}: item {} is spiked".format(c["name"], key))
        if c.get("pinned") and c["pinned"] not in c["items"]:
            problems.append("content list {}: pinned item is not in its items".format(c["name"]))
    for w in data.CONTENT_LIST_WEBHOOKS:
        for name in w.get("excluded_lists", []):
            if name not in lists:
                problems.append("webhook {}: unknown list {!r}".format(w["url"], name))
    products = {p["name"] for p in data.PRODUCTS}
    for sub in data.SUBSCRIBERS + [data.SNAPSHOT_SUBSCRIBER]:
        for name in sub.get("products", []) + sub.get("api_products", []):
            if name not in products:
                problems.append("subscriber {}: unknown product {!r}".format(sub["name"], name))
    for ss in data.SAVED_SEARCHES:
        for user in [ss["owner"], ss.get("subscribe")]:
            if user and user not in known_users:
                problems.append("saved search {}: unknown user {!r}".format(ss["name"], user))
    if sum(1 for m in data.SYSTEM_MESSAGES if m["is_active"]) > 1:
        problems.append("system messages: more than one is active")
    for m in data.SYSTEM_MESSAGES:
        if len(m["message"]) > 200:
            problems.append("system message {}: the server allows 200 characters".format(m["message_title"]))
    for name in data.DESK_SETTINGS:
        if name not in desks:
            problems.append("desk settings: unknown desk {!r}".format(name))
    tag_codes = {i["qcode"] for i in data.AVAILABILITY_TAGS["items"]}
    for user, pattern in data.AVAILABILITY.items():
        if user not in known_users:
            problems.append("availability: unknown user {!r}".format(user))
        for tag in pattern["tags"]:
            if tag not in tag_codes:
                problems.append("availability {}: unknown tag {!r}".format(user, tag))
        days = [d for days, _, _ in pattern["days"] for d in days]
        if len(days) != len(set(days)) or not set(days) <= set(data.WEEKDAYS):
            problems.append("availability {}: days must be distinct weekday names".format(user))
    for o in data.AVAILABILITY_OVERRIDES:
        if o["user"] not in data.AVAILABILITY:
            problems.append("availability override: {} has no default week".format(o["user"]))
    bm = data.BODY_MEDIA
    if bm["item"] not in articles or articles[bm["item"]].get("action"):
        problems.append("body media: {} must be an unpublished article".format(bm["item"]))
    elif not 0 < bm["after_paragraph"] <= len(articles[bm["item"]]["body"]):
        problems.append("body media: after_paragraph out of range")
    if bm["picture"] not in {p["key"] for p in data.PICTURES}:
        problems.append("body media: unknown picture {!r}".format(bm["picture"]))
    if bm["item"] in packaged or bm["item"] in locked:
        problems.append("body media: {} is packaged or locked".format(bm["item"]))
    for c in data.COMMENTS:
        if c["item"] not in articles:
            problems.append("comment: unknown item {!r}".format(c["item"]))
        if c["user"] not in known_users:
            problems.append("comment: unknown user {!r}".format(c["user"]))

    if problems:
        raise SeedError("seed_data.py has problems:\n  - " + "\n  - ".join(problems))


# ---- generated pictures -----------------------------------------------------------------------------

SCENES = {
    # sky top, sky bottom, sun, far land, near land, water
    "regatta": ((96, 160, 220), (196, 226, 245), (255, 250, 230), (120, 150, 130), None, (40, 105, 170)),
    "marathon": ((250, 170, 110), (255, 226, 170), (255, 244, 214), (150, 110, 100), (90, 70, 70), (210, 150, 120)),
    "rowing": ((170, 186, 196), (226, 230, 228), (250, 246, 236), (124, 142, 136), (84, 104, 96), (150, 170, 172)),
    "stadium": ((14, 22, 48), (52, 60, 98), None, (30, 34, 52), (18, 20, 30), None),
}


def lerp(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def render_scene(scene, seed):
    """Draw a simple photo-like landscape for a picture item. Needs Pillow."""
    rng = random.Random(seed)
    width, height = 1600, 1066
    sky_top, sky_bottom, sun, far, near, water = SCENES[scene]
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    horizon = int(height * (0.62 if water else 0.72))

    for y in range(horizon):
        draw.line([(0, y), (width, y)], fill=lerp(sky_top, sky_bottom, y / horizon))
    if sun:
        cx, cy, r = int(width * rng.uniform(0.2, 0.8)), int(horizon * rng.uniform(0.35, 0.7)), 70
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=sun)

    def ridge(base, amplitude, color, phase):
        points = [(0, height)]
        for x in range(0, width + 20, 20):
            y = base - amplitude * (0.6 * math.sin(x / 260.0 + phase) + 0.4 * math.sin(x / 97.0 + phase * 2))
            points.append((x, int(y)))
        points.append((width, height))
        draw.polygon(points, fill=color)

    ridge(horizon, 45, far, rng.uniform(0, 6))
    if water:
        for y in range(horizon, height):
            t = (y - horizon) / (height - horizon)
            draw.line([(0, y), (width, y)], fill=lerp(lerp(water, sky_bottom, 0.25), water, t))
        for _ in range(160):
            x, y = rng.randint(0, width), rng.randint(horizon + 5, height)
            draw.line([(x, y), (x + rng.randint(20, 90), y)], fill=lerp(water, (255, 255, 255), 0.35))
    if near:
        ridge(height - 60, 50, near, rng.uniform(0, 6))

    if scene == "regatta":
        for _ in range(5):
            x, y = rng.randint(150, width - 150), rng.randint(horizon + 40, height - 120)
            s = rng.randint(70, 140)
            draw.polygon([(x, y), (x, y - s), (x + int(s * 0.55), y)], fill=(250, 250, 248))
            draw.polygon([(x - 6, y - int(s * 0.7)), (x - 6, y), (x - int(s * 0.35), y)], fill=(235, 235, 230))
            draw.rectangle([x - int(s * 0.4), y, x + int(s * 0.6), y + 12], fill=(30, 40, 60))
    elif scene == "rowing":
        for i in range(3):
            y = horizon + 70 + i * 90
            x = rng.randint(200, width - 700)
            draw.rectangle([x, y, x + 520, y + 10], fill=(200, 60, 50))
            for oar in range(8):
                ox = x + 40 + oar * 60
                draw.line([(ox, y + 5), (ox - 30, y + 45)], fill=(40, 40, 40), width=4)
    elif scene == "stadium":
        towers = (220, 640, 1060, 1440)
        glow = Image.new("RGB", (width, height))
        glow_draw = ImageDraw.Draw(glow)
        for x in towers:
            glow_draw.ellipse([x - 240, -40, x + 240, 330], fill=(120, 116, 84))
        img = ImageChops.add(img, glow.filter(ImageFilter.GaussianBlur(70)))
        draw = ImageDraw.Draw(img)
        for x in towers:
            draw.rectangle([x - 6, 160, x + 6, horizon], fill=(40, 44, 60))
            draw.rectangle([x - 70, 120, x + 70, 170], fill=(255, 252, 230))
        draw.rectangle([0, horizon, width, height], fill=(40, 110, 60))
        for x in range(0, width, 160):
            draw.rectangle([x, horizon, x + 80, height], fill=(46, 122, 68))
    elif scene == "marathon":
        x = 0
        while x < width:
            w = rng.randint(60, 140)
            draw.rectangle(
                [x, horizon - rng.randint(90, 260), x + w, horizon], fill=lerp(far, sky_bottom, rng.uniform(0.0, 0.4))
            )
            x += w + rng.randint(4, 30)

    img = img.filter(ImageFilter.GaussianBlur(1.2))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=88)
    return out.getvalue()


class PictureSource:
    def __init__(self, images_dir):
        self.files = []
        if images_dir:
            if not os.path.isdir(images_dir):
                raise SeedError("--images-dir {} is not a folder".format(images_dir))
            self.files = sorted(
                os.path.join(images_dir, f) for f in os.listdir(images_dir) if f.lower().endswith(IMAGE_EXTENSIONS)
            )
            if not self.files:
                raise SeedError("No .jpg/.jpeg/.png files in {}".format(images_dir))

    @property
    def available(self):
        return bool(self.files) or Image is not None

    def describe(self):
        if self.files:
            return "{} file(s) from --images-dir".format(len(self.files))
        if Image is not None:
            return "generated with Pillow"
        return "skipped: Pillow is not installed and no --images-dir was given"

    def get(self, spec, index):
        if self.files:
            path = self.files[index % len(self.files)]
            with open(path, "rb") as fh:
                content = fh.read()
            mimetype = "image/png" if path.lower().endswith(".png") else "image/jpeg"
            return content, os.path.basename(path), mimetype
        return render_scene(spec["scene"], spec["key"]), spec["key"] + ".jpg", "image/jpeg"


# ---- payloads ---------------------------------------------------------------------------------------


def article_payload(spec, ctx):
    versioncreated = utcnow() - datetime.timedelta(minutes=spec.get("age_minutes", 30))
    firstcreated = versioncreated - datetime.timedelta(minutes=spec.get("created_before_minutes", 45))
    place = data.PLACES[spec["place"]]
    author_id = ctx["user_ids"][spec["author"]]
    author_name = ctx["display_names"][spec["author"]]
    payload = {
        "guid": guid_for(spec["key"]),
        "type": "text",
        "profile": ctx["profile_id"],
        "language": "en",
        "state": "submitted" if spec["stage"] == "Incoming" else "in_progress",
        "slugline": spec["slugline"],
        "headline": spec["headline"],
        "abstract": spec["abstract"],
        "body_html": "".join("<p>{}</p>".format(html_escape(p)) for p in spec["body"]),
        "byline": author_name,
        "authors": [
            {
                "_id": [author_id, "writer"],
                "role": "writer",
                "name": "Writer",
                "parent": author_id,
                "sub_label": author_name,
            }
        ],
        "urgency": spec["urgency"],
        "priority": spec["priority"],
        "genre": [{"qcode": spec["genre"], "name": data.GENRES[spec["genre"]]}],
        "anpa_category": category_list(spec["category"]),
        "subject": subject_list(spec["subjects"]),
        "dateline": {
            "located": {
                "city": place["city"],
                "city_code": place["city"],
                "country": place["country"],
                "tz": place["tz"],
                "dateline": "city",
            },
            "date": fmt(versioncreated),
            "source": data.NEWSROOM["source"],
            "text": "{}, {} {} {} -".format(
                place["city"].upper(), versioncreated.strftime("%b"), versioncreated.day, data.NEWSROOM["source"]
            ),
        },
        "firstcreated": fmt(firstcreated),
        "versioncreated": fmt(versioncreated),
        "task": {
            "desk": ctx["desk_ids"][spec["desk"]],
            "stage": ctx["stage_ids"][(spec["desk"], spec["stage"])],
            "user": author_id,
        },
    }
    if spec.get("ednote"):
        payload["ednote"] = spec["ednote"]
    if not payload["profile"]:
        del payload["profile"]
    return payload


def html_escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def publish_payload(spec):
    """Body for PATCH /archive/publish/<id>, or None when the spec is not published or scheduled."""
    action = spec.get("action")
    if action not in ("publish", "schedule"):
        return None
    payload = {}
    if action == "schedule":
        payload["publish_schedule"] = wall_time(spec["publish_at"])
    if spec.get("embargo"):
        payload["embargo"] = wall_time(spec["embargo"])
    if payload:
        payload["schedule_settings"] = schedule_settings()
    else:
        payload["state"] = "published"
    return payload


# ---- seeding ----------------------------------------------------------------------------------------


class Seeder:
    def __init__(self, args):
        self.args = args
        self.api_url = args.api_url.rstrip("/")
        self.admin = None
        self.sessions = {}
        self.users = {}  # username -> user doc
        self.user_ids = {}
        self.display_names = {}
        self.role_ids = {}
        self.desks = {}  # name -> desk doc
        self.desk_ids = {}
        self.stage_ids = {}  # (desk name, stage name) -> id
        self.profile_id = None
        self.template_id = None
        self.created_desks = set()
        self.seed_usernames = {u["username"] for u in data.USERS}
        self.users_by_name = {u["username"]: u for u in data.USERS}

    # -- sessions

    def connect(self):
        self.admin = login(self.api_url, self.args.user, self.args.password)
        self.sessions[self.args.user] = self.admin
        log("login", "user", self.args.user)

    def client_for(self, username):
        username = self.args.user if username == "admin" else username
        if username not in self.sessions:
            # Every user created by this script, and the e2e snapshot users, use their username as password.
            self.sessions[username] = login(self.api_url, username, username)
            log("login", "user", username)
        return self.sessions[username]

    def ctx(self):
        return {
            "user_ids": self.user_ids,
            "display_names": self.display_names,
            "desk_ids": self.desk_ids,
            "stage_ids": self.stage_ids,
            "profile_id": self.profile_id,
        }

    # -- lookups

    def find_user(self, username):
        username = self.args.user if username == "admin" else username
        return self.admin.find_one("/users", {"username": username}, show_inactive=1, show_disabled=1)

    def remember_user(self, key, doc):
        self.users[key] = doc
        self.user_ids[key] = str(doc["_id"])
        name = doc.get("display_name") or "{} {}".format(doc.get("first_name", ""), doc.get("last_name", "")).strip()
        self.display_names[key] = name or doc.get("username", key)

    def load_reference_data(self):
        profile = self.admin.find_one("/content_types", {"label": "Story"})
        self.profile_id = str(profile["_id"]) if profile else None
        template = self.admin.find_one("/content_templates", {"template_name": "story"})
        self.template_id = str(template["_id"]) if template else None
        log("found", "profile", "Story" if profile else "(none, items use the server default)")

    def get_item(self, key):
        return self.admin.get_optional(item_path(guid_for(key)))

    # -- roles

    def ensure_roles(self):
        for spec in data.ROLES:
            doc = self.admin.find_one("/roles", {"name": spec["name"]})
            if doc:
                log("skip", "role", spec["name"], "exists")
            else:
                doc = self.admin.post(
                    "/roles",
                    {
                        "name": spec["name"],
                        "description": spec["description"],
                        "privileges": {p: 1 for p in spec["privileges"]},
                        "is_default": False,
                    },
                )
                log("create", "role", spec["name"])
            self.role_ids[spec["name"]] = str(doc["_id"])

    # -- categories vocabulary

    def desired_categories(self, items):
        ours = {c["qcode"]: c for c in data.CATEGORIES}
        result = [{"is_active": True, "name": c["name"], "qcode": c["qcode"], "subject": ""} for c in data.CATEGORIES]
        for item in items:
            if item.get("qcode") in ours:
                continue
            item = dict(item)
            if item.get("qcode") in data.HIDDEN_CATEGORY_QCODES:
                item["is_active"] = False
            result.append(item)
        return result

    def ensure_categories(self):
        voc = self.admin.get_optional("/vocabularies/categories")
        if voc is None:
            log("warn", "vocab", "categories", "vocabulary not found, categories left out")
            return
        desired = self.desired_categories(voc.get("items", []))

        def normalized(items):
            # The server drops `is_active: true` when it stores the items; missing means active.
            return [dict({"is_active": True}, **item) for item in items]

        if normalized(desired) == normalized(voc.get("items", [])):
            log("skip", "vocab", "categories", "up to date")
            return
        self.admin.patch("/vocabularies/categories", {"items": desired}, voc["_etag"])
        log("update", "vocab", "categories", ", ".join(c["name"] for c in data.CATEGORIES))

    # -- users

    def ensure_users(self):
        for spec in data.USERS:
            doc = self.find_user(spec["username"])
            role_id = self.role_ids[spec["role"]]
            if doc is None:
                first, last = spec["first_name"], spec["last_name"]
                doc = self.admin.post(
                    "/users",
                    {
                        "username": spec["username"],
                        "password": spec["username"],
                        "email": "{}.{}@{}".format(first.lower(), last.lower(), data.NEWSROOM["email_domain"]),
                        "first_name": first,
                        "last_name": last,
                        "display_name": "{} {}".format(first, last),
                        "sign_off": spec["sign_off"],
                        "byline": "{} {}".format(first, last),
                        "job_title": spec["job_title"],
                        "user_type": "user",
                        "role": role_id,
                        "language": "en",
                        "is_author": True,
                        "is_active": True,
                        "is_enabled": True,
                        "needs_activation": False,
                    },
                )
                doc = self.admin.get("/users/" + str(doc["_id"]))
                log("create", "user", spec["username"], "{} ({})".format(doc.get("display_name"), spec["role"]))
            else:
                updates = {}
                if not doc.get("is_enabled", True) or not doc.get("is_active", True):
                    updates.update({"is_enabled": True, "is_active": True})
                if str(doc.get("role") or "") != role_id:
                    updates["role"] = role_id
                if updates:
                    self.admin.patch("/users/" + str(doc["_id"]), updates, doc["_etag"])
                    doc = self.admin.get("/users/" + str(doc["_id"]))
                    log("update", "user", spec["username"], ", ".join(sorted(updates)))
                else:
                    log("skip", "user", spec["username"], "exists")
            self.remember_user(spec["username"], doc)

        for username in data.SNAPSHOT_USERS:
            doc = self.find_user(username)
            if doc is None:
                if self.is_referenced(username):
                    raise SeedError("User {!r} from the e2e snapshot is missing but referenced in seed_data.py".format(username))
                continue
            self.remember_user(username, doc)

    def is_referenced(self, username):
        refs = [a["author"] for a in data.ARTICLES] + [p["author"] for p in data.PICTURES + data.PACKAGES]
        refs += [m["user"] for m in data.MARKS + data.LOCKS]
        refs += [m for d in all_desks(self.args.send_and_duplicate_desk) for m in d.get("members", [])]
        return username in refs

    # -- desks and stages

    def load_stages(self, desk_id):
        stages = self.admin.find_all("/stages", {"desk": desk_id})
        return sorted(stages, key=lambda s: s.get("desk_order", 0))

    def ensure_desks(self):
        for spec in all_desks(self.args.send_and_duplicate_desk):
            desk = self.admin.find_one("/desks", {"name": spec["name"]})
            member_ids = [self.user_ids[m] for m in spec.get("members", [])]
            if desk is None:
                payload = {
                    "name": spec["name"],
                    "description": spec.get("description", ""),
                    "desk_type": spec.get("desk_type", "production"),
                    "source": spec.get("source", spec["name"]),
                    "members": [{"user": uid} for uid in member_ids],
                    "desk_metadata": {},
                    "preserve_published_content": False,
                }
                if self.profile_id:
                    payload["default_content_profile"] = self.profile_id
                if self.template_id:
                    payload["default_content_template"] = self.template_id
                desk = self.admin.post("/desks", payload)
                self.created_desks.add(spec["name"])
                log("create", "desk", spec["name"], spec.get("desk_type", "production"))
            else:
                log("found", "desk", spec["name"])
            desk_id = str(desk["_id"])

            loaded = self.load_stages(desk_id)
            stages = {s["name"]: s for s in loaded}
            for stage_spec in spec["stages"]:
                stage = stages.get(stage_spec["name"])
                description = stage_spec.get("description")
                default = stage_spec.get("default")
                if stage is None and default:
                    # the server created this stage with its own name; rename it
                    flag = "working_stage" if default == "working" else "default_incoming"
                    stage = next((s for s in loaded if s.get(flag)), None)
                    if stage is not None and stage["name"] != stage_spec["name"]:
                        patch = {"name": stage_spec["name"]}
                        if description:
                            patch["description"] = description
                        self.admin.patch("/stages/" + str(stage["_id"]), patch, stage["_etag"])
                        log("update", "stage", "{} / {}".format(spec["name"], stage_spec["name"]), "renamed from " + stage["name"])
                        stage = dict(stage, **patch)
                        continue
                if stage is None:
                    payload = {"name": stage_spec["name"], "desk": desk_id, "is_visible": True}
                    if description:
                        payload["description"] = description
                    self.admin.post("/stages", payload)
                    log("create", "stage", "{} / {}".format(spec["name"], stage_spec["name"]))
                elif description and not spec.get("snapshot") and stage.get("description") != description:
                    self.admin.patch("/stages/" + str(stage["_id"]), {"description": description}, stage["_etag"])
                    log("update", "stage", "{} / {}".format(spec["name"], stage_spec["name"]), "description")
                else:
                    log("skip", "stage", "{} / {}".format(spec["name"], stage_spec["name"]), "exists")

            ordered = self.load_stages(desk_id)
            for stage in ordered:
                self.stage_ids[(spec["name"], stage["name"])] = str(stage["_id"])

            desk = self.admin.get("/desks/" + desk_id)
            updates = {}
            current = [str(m["user"]) for m in desk.get("members") or []]
            missing = [uid for uid in member_ids if uid not in current]
            if missing:
                updates["members"] = [{"user": uid} for uid in current + missing]
            if spec.get("monitoring"):
                groups = [{"_id": str(s["_id"]), "type": "stage", "max_items": 10} for s in ordered]
                groups.append({"_id": desk_id + ":output", "type": "deskOutput", "max_items": 10})
                groups.append({"_id": desk_id + ":scheduled", "type": "scheduledDeskOutput", "max_items": 10})
                if desk.get("monitoring_settings") != groups:
                    updates["monitoring_settings"] = groups
            if updates:
                self.admin.patch("/desks/" + desk_id, updates, desk["_etag"])
                desk = self.admin.get("/desks/" + desk_id)
                detail = []
                if "members" in updates:
                    detail.append("members +" + ", ".join(self.username_for(uid) for uid in missing))
                if "monitoring_settings" in updates:
                    detail.append("monitoring groups incl. scheduled output")
                log("update", "desk", spec["name"], "; ".join(detail))
            self.desks[spec["name"]] = desk
            self.desk_ids[spec["name"]] = desk_id

    def username_for(self, user_id):
        for name, uid in self.user_ids.items():
            if uid == user_id:
                return name
        return user_id

    def check_member(self, username, desk_name, what):
        uid = self.user_ids[username]
        members = [str(m["user"]) for m in self.desks[desk_name].get("members") or []]
        if uid not in members:
            raise SeedError("{}: user {} is not a member of desk {} on the server".format(what, username, desk_name))

    def ensure_default_desks(self):
        wanted = [(u["username"], u.get("default_desk")) for u in data.USERS]
        wanted.append(("admin", data.ADMIN_DEFAULT_DESK))
        for username, desk_name in wanted:
            if not desk_name:
                continue
            doc = self.admin.get("/users/" + self.user_ids[username])
            if str(doc.get("desk") or "") == self.desk_ids[desk_name]:
                log("skip", "user", username, "default desk {}".format(desk_name))
                continue
            self.admin.patch("/users/" + self.user_ids[username], {"desk": self.desk_ids[desk_name]}, doc["_etag"])
            log("update", "user", username, "default desk {}".format(desk_name))

    # -- items

    def restore_if_spiked(self, item, spec, kind, label):
        if item.get("state") != "spiked" or spec.get("action") == "spike":
            return item
        task = {"desk": self.desk_ids[spec["desk"]], "stage": self.stage_ids[(spec["desk"], spec["stage"])]}
        self.admin.patch(item_path(item["_id"], "unspike"), {"task": task}, item["_etag"])
        log("unspike", kind, label, "back to {} / {}".format(spec["desk"], spec["stage"]))
        return self.admin.get(item_path(item["_id"]))

    def ensure_articles(self):
        for spec in data.ARTICLES:
            item = self.get_item(spec["key"])
            if item is None:
                self.check_member(spec["author"], spec["desk"], "article " + spec["key"])
                client = self.client_for(spec["author"])
                client.post("/archive", article_payload(spec, self.ctx()))
                item = self.admin.get(item_path(guid_for(spec["key"])))
                log("create", "article", spec["slugline"], "{} / {} by {}".format(spec["desk"], spec["stage"], spec["author"]))
            else:
                log("skip", "article", spec["slugline"], "exists ({})".format(item.get("state")))
                item = self.restore_if_spiked(item, spec, "article", spec["slugline"])
            self.apply_action(spec, item)

    def apply_action(self, spec, item):
        action = spec.get("action")
        state = item.get("state")
        if action == "spike":
            if state == "spiked":
                return
            self.admin.patch(item_path(item["_id"], "spike"), {"state": "spiked"}, item["_etag"])
            log("spike", "article", spec["slugline"])
            return
        payload = publish_payload(spec)
        if payload is None:
            return
        if state in PUBLISHED_STATES or state == "scheduled":
            if action == "schedule" and state != "scheduled":
                log("warn", "article", spec["slugline"], "already {}, not scheduled again".format(state))
            return
        if item.get("lock_user"):
            self.admin.post(item_path(item["_id"], "unlock"), {})
            item = self.admin.get(item_path(item["_id"]))
        self.admin.patch(item_path(item["_id"], "publish"), payload, item["_etag"])
        detail = []
        if payload.get("publish_schedule"):
            detail.append("for " + payload["publish_schedule"][:16].replace("T", " "))
        if payload.get("embargo"):
            detail.append("embargo " + payload["embargo"][:16].replace("T", " "))
        if detail:
            detail.append(payload["schedule_settings"]["time_zone"] or "UTC")
        log("schedule" if action == "schedule" else "publish", "article", spec["slugline"], " ".join(detail))

    def ensure_pictures(self, source):
        if not data.PICTURES:
            return
        if not source.available:
            log("skip", "picture", "all", source.describe())
            return
        for index, spec in enumerate(data.PICTURES):
            item = self.get_item(spec["key"])
            client = self.client_for(spec["author"])
            if item is None:
                self.check_member(spec["author"], spec["desk"], "picture " + spec["key"])
                content, filename, mimetype = source.get(spec, index)
                fields = {
                    "guid": guid_for(spec["key"]),
                    "headline": spec["headline"],
                    "slugline": spec["slugline"],
                    "description_text": spec["description_text"],
                    "alt_text": spec["alt_text"],
                    "byline": self.display_names[spec["author"]],
                }
                client.post_multipart("/archive", fields, "media", filename, content, mimetype)
                item = self.admin.get(item_path(guid_for(spec["key"])))
                log("upload", "picture", spec["headline"], "{} ({})".format(filename, source.describe()))
            else:
                log("skip", "picture", spec["headline"], "exists ({})".format(item.get("state")))
                item = self.restore_if_spiked(item, spec, "picture", spec["headline"])
            task = item.get("task") or {}
            if not task.get("desk"):
                client.post(
                    item_path(item["_id"], "move"),
                    {"task": {"desk": self.desk_ids[spec["desk"]], "stage": self.stage_ids[(spec["desk"], spec["stage"])]}},
                )
                log("move", "picture", spec["headline"], "to {} / {}".format(spec["desk"], spec["stage"]))

    def ensure_packages(self):
        for spec in data.PACKAGES:
            item = self.get_item(spec["key"])
            if item is not None:
                log("skip", "package", spec["slugline"], "exists ({})".format(item.get("state")))
                self.restore_if_spiked(item, spec, "package", spec["slugline"])
                continue
            refs = []
            for key in spec["items"]:
                member = self.get_item(key)
                if member is None:
                    raise SeedError("package {}: item {} was not created".format(spec["key"], key))
                refs.append(
                    {
                        "residRef": member["_id"],
                        "headline": member.get("headline"),
                        "slugline": member.get("slugline"),
                        "location": "archive",
                        "itemClass": "icls:text",
                    }
                )
            self.check_member(spec["author"], spec["desk"], "package " + spec["key"])
            author_id = self.user_ids[spec["author"]]
            payload = {
                "guid": guid_for(spec["key"]),
                "type": "composite",
                "state": "in_progress",
                "language": "en",
                "headline": spec["headline"],
                "slugline": spec["slugline"],
                "abstract": spec["abstract"],
                "byline": self.display_names[spec["author"]],
                "anpa_category": category_list(spec["category"]),
                "subject": subject_list(spec["subjects"]),
                "groups": [
                    {"id": "root", "role": "grpRole:NEP", "refs": [{"idRef": "main"}]},
                    {"id": "main", "role": "grpRole:main", "refs": refs},
                ],
                "task": {
                    "desk": self.desk_ids[spec["desk"]],
                    "stage": self.stage_ids[(spec["desk"], spec["stage"])],
                    "user": author_id,
                },
            }
            self.client_for(spec["author"]).post("/archive", payload)
            log("create", "package", spec["slugline"], "{} item(s) on {} / {}".format(len(refs), spec["desk"], spec["stage"]))

    def ensure_marks(self):
        for mark in data.MARKS:
            item = self.get_item(mark["item"])
            if item is None:
                raise SeedError("mark: item {} does not exist".format(mark["item"]))
            uid = self.user_ids[mark["user"]]
            if str(item.get("marked_for_user") or "") == uid:
                log("skip", "mark", item.get("slugline"), "already marked for {}".format(mark["user"]))
                continue
            if item.get("lock_user") and str(item["lock_user"]) != self.admin.user_id:
                self.admin.post(item_path(item["_id"], "unlock"), {})
                item = self.admin.get(item_path(item["_id"]))
            self.admin.patch(item_path(item["_id"]), {"marked_for_user": uid}, item["_etag"])
            log("mark", "article", item.get("slugline"), "for {}".format(mark["user"]))

    def ensure_locks(self):
        for lock in data.LOCKS:
            item = self.get_item(lock["item"])
            if item is None:
                raise SeedError("lock: item {} does not exist".format(lock["item"]))
            uid = self.user_ids[lock["user"]]
            if str(item.get("lock_user") or "") == uid:
                log("skip", "lock", item.get("slugline"), "already locked by {}".format(lock["user"]))
                continue
            if item.get("lock_user"):
                self.admin.post(item_path(item["_id"], "unlock"), {})
            self.client_for(lock["user"]).post(item_path(item["_id"], "lock"), {"lock_action": "edit"})
            log("lock", "article", item.get("slugline"), "by {}".format(lock["user"]))

    # -- settings and supporting data

    def find_named(self, path, value, field="name", client=None, **match):
        """Look a document up by name in Python, so it works for resources whose `where` support differs."""
        items = (client or self.admin).get(path, max_results=200).get("_items", [])
        for item in items:
            if item.get(field) == value and all(str(item.get(k) or "") == str(v) for k, v in match.items()):
                return item
        return None

    def ensure_story_profile(self):
        found = self.admin.find_one("/content_types", {"label": "Story"})
        if found is None:
            log("warn", "profile", "Story", "not found, body field left as it is")
            return
        profile = self.admin.get("/content_types/" + str(found["_id"]))
        editor, schema = dict(profile.get("editor") or {}), dict(profile.get("schema") or {})
        body_editor, body_schema = dict(editor.get("body_html") or {}), dict(schema.get("body_html") or {})
        changes = []
        if body_editor.get("formatOptions") != data.STORY_BODY["format_options"]:
            body_editor["formatOptions"] = list(data.STORY_BODY["format_options"])
            changes.append("formatting options")
        if body_schema.get("maxlength") != data.STORY_BODY["maxlength"]:
            body_schema["maxlength"] = data.STORY_BODY["maxlength"]
            changes.append("maxlength {}".format(data.STORY_BODY["maxlength"]))
        if not changes:
            log("skip", "profile", "Story", "body field up to date")
            return
        editor["body_html"], schema["body_html"] = body_editor, body_schema
        self.admin.patch("/content_types/" + str(profile["_id"]), {"editor": editor, "schema": schema}, profile["_etag"])
        log("update", "profile", "Story", "body " + ", ".join(changes))

    def ensure_custom_blocks(self):
        for spec in data.CUSTOM_BLOCKS:
            if self.admin.get_optional("/vocabularies/" + spec["_id"]) is not None:
                log("skip", "block", spec["display_name"], "exists")
                continue
            blocks = [
                {"key": "{}{}".format(spec["_id"][:3], i), "text": line, "type": "unstyled", "depth": 0,
                 "inlineStyleRanges": [], "entityRanges": [], "data": {}}
                for i, line in enumerate(spec["template"])
            ]
            self.admin.post(
                "/vocabularies",
                {
                    "_id": spec["_id"],
                    "display_name": spec["display_name"],
                    "field_type": "editor-block",
                    "type": "manageable",
                    "items": [],
                    "service": {"all": 1},
                    "field_options": {
                        "formatting_options": spec["formatting_options"],
                        "template": [{"blocks": blocks, "entityMap": {}}],
                    },
                },
            )
            log("create", "block", spec["display_name"], "custom block vocabulary " + spec["_id"])

    def ensure_body_media(self):
        spec = data.BODY_MEDIA
        item = self.get_item(spec["item"])
        if (item.get("associations") or {}).get("editor_0"):
            log("skip", "media", item.get("slugline"), "picture already in the body")
            return
        picture = self.get_item(spec["picture"])
        if picture is None:
            log("warn", "media", item.get("slugline"), "picture {} missing (no Pillow?), left out".format(spec["picture"]))
            return
        media = {k: v for k, v in picture.items() if not k.startswith("_") or k in ("_id", "_type")}
        media["description_text"] = spec["caption"]
        paragraphs = next(a["body"] for a in data.ARTICLES if a["key"] == spec["item"])
        blocks = [
            {"key": "p{}".format(i), "text": text, "type": "unstyled", "depth": 0,
             "inlineStyleRanges": [], "entityRanges": [], "data": {}}
            for i, text in enumerate(paragraphs)
        ]
        blocks.insert(spec["after_paragraph"], {
            "key": "media0", "text": " ", "type": "atomic", "depth": 0, "inlineStyleRanges": [],
            "entityRanges": [{"offset": 0, "length": 1, "key": 0}], "data": {},
        })
        raw = {"blocks": blocks, "entityMap": {"0": {"type": "MEDIA", "mutability": "MUTABLE", "data": {"media": media}}}}
        href = ((media.get("renditions") or {}).get("baseImage") or {}).get("href", "")
        embed = (
            '<!-- EMBED START Image {{id: "editor_0"}} --><figure><img src="{}" alt="{}" /><figcaption>{}</figcaption>'
            '</figure><!-- EMBED END Image {{id: "editor_0"}} -->'
        ).format(href, html_escape(media.get("alt_text", "")), html_escape(spec["caption"]))
        html = ["<p>{}</p>".format(html_escape(t)) for t in paragraphs]
        html.insert(spec["after_paragraph"], embed)
        # editor3 reads the body from fields_meta (draft.js) when the profile has media blocks; the entity
        # with key N is stored as association editor_N.
        fields_meta = dict(item.get("fields_meta") or {}, body_html={"draftjsState": [raw]})
        if item.get("lock_user"):
            self.admin.post(item_path(item["_id"], "unlock"), {})
            item = self.admin.get(item_path(item["_id"]))
        self.admin.patch(
            item_path(item["_id"]),
            {"body_html": "".join(html), "associations": {"editor_0": media}, "fields_meta": fields_meta},
            item["_etag"],
        )
        log("update", "media", item.get("slugline"), "picture {} after paragraph {}".format(
            picture.get("slugline"), spec["after_paragraph"]))

    def ensure_crop_sizes(self):
        voc = self.admin.get_optional("/vocabularies/crop_sizes")
        if voc is None:
            log("warn", "vocab", "crop_sizes", "not found")
            return
        names = {i.get("name") for i in voc.get("items", [])}
        missing = [dict(c) for c in data.CROP_SIZES if c["name"] not in names]
        if not missing:
            log("skip", "vocab", "crop_sizes", "up to date")
            return
        self.admin.patch("/vocabularies/crop_sizes", {"items": voc.get("items", []) + missing}, voc["_etag"])
        log("update", "vocab", "crop_sizes", "added " + ", ".join(c["name"] for c in missing))

    def ensure_dictionary(self):
        spec = data.DICTIONARY
        doc = self.find_named("/dictionaries", spec["name"], language_id=spec["language_id"])
        if doc is not None:
            full = self.admin.get("/dictionaries/" + str(doc["_id"]))
            if full.get("content"):
                log("skip", "dict", spec["name"], "{} words".format(len(full["content"])))
                return
        else:
            doc = self.admin.post("/dictionaries", {"name": spec["name"], "language_id": spec["language_id"]})
        words = dictionary_words(spec.get("system_words"))
        doc = self.admin.get("/dictionaries/" + str(doc["_id"]))
        # The server only turns `content_list` into words on update, not on create.
        self.admin.patch("/dictionaries/" + str(doc["_id"]), {"content_list": json.dumps(words)}, doc["_etag"])
        log("create", "dict", spec["name"], "{} words".format(len(words)))

    def ensure_templates(self):
        for spec in data.TEMPLATES:
            doc = self.admin.find_one("/content_templates", {"template_name": spec["template_name"]})
            if doc is None:
                log("warn", "template", spec["template_name"], "not in the snapshot, left out")
                continue
            body = "<p>{}</p>".format(html_escape(spec["body"]))
            current = doc.get("data") or {}
            if current.get("headline") == spec["headline"] and current.get("body_html") == body:
                log("skip", "template", spec["template_name"], "up to date")
                continue
            self.admin.patch(
                "/content_templates/" + str(doc["_id"]),
                {"data": dict(current, headline=spec["headline"], body_html=body)},
                doc["_etag"],
            )
            log("update", "template", spec["template_name"], spec["headline"])

    def ensure_recent_templates(self):
        spec = data.RECENT_TEMPLATES
        user_id = self.admin.user_id if spec["user"] == "admin" else self.user_ids[spec["user"]]
        desk_id = self.desk_ids[spec["desk"]]
        ids = []
        for tpl in spec["templates"]:
            # The server stores template names in lower case.
            doc = self.admin.find_one("/content_templates", {"template_name": tpl["template_name"].lower()})
            if doc is None:
                doc = self.admin.post("/content_templates", {
                    "template_name": tpl["template_name"],
                    "template_type": "create",
                    "is_public": tpl["is_public"],
                    "template_desks": [desk_id] if tpl["is_public"] else [],
                    "user": user_id,
                    "data": {
                        "profile": self.profile_id, "type": "text",
                        "headline": tpl["headline"], "body_html": "<p>{}</p>".format(html_escape(tpl["body"])),
                    },
                })
                log("create", "template", tpl["template_name"], "desk" if tpl["is_public"] else "personal")
            else:
                log("skip", "template", tpl["template_name"], "exists")
            ids.append(str(doc["_id"]))
        client = self.client_for(spec["user"])
        prefs = client.get("/preferences/" + client.session_id)
        recent = dict((prefs.get("user_preferences") or {}).get("templates:recent") or {})
        if recent.get(desk_id) == ids:
            log("skip", "prefs", spec["user"], "recent templates on " + spec["desk"])
            return
        recent[desk_id] = ids
        client.patch("/preferences/" + client.session_id, {"user_preferences": {"templates:recent": recent}}, prefs["_etag"])
        log("update", "prefs", spec["user"], "recent templates on " + spec["desk"])

    def ensure_desk_settings(self):
        voc = None
        if any(s.get("preferred_categories") for s in data.DESK_SETTINGS.values()):
            voc = self.admin.get_optional("/vocabularies/categories")
            if voc is not None and not voc.get("preffered_items"):
                # sic: the server field is spelled `preffered_items`
                self.admin.patch("/vocabularies/categories", {"preffered_items": True}, voc["_etag"])
                log("update", "vocab", "categories", "available in user/desk preferences")
        for name, spec in data.DESK_SETTINGS.items():
            desk = self.admin.get("/desks/" + self.desk_ids[name])
            updates = {}
            if spec.get("email") and desk.get("email") != spec["email"]:
                updates["email"] = spec["email"]
            if spec.get("preferred_categories"):
                # The desk settings chips render each item's `name`, so store qcode and name as the
                # client does; bare qcodes show as empty chips.
                names = {i.get("qcode"): i.get("name") for i in (voc or {}).get("items", [])}
                wanted = {"categories": [{"qcode": q, "name": names.get(q, q)} for q in spec["preferred_categories"]]}
                current = desk.get("preferred_cv_items") or {}
                if current.get("categories") != wanted["categories"]:
                    updates["preferred_cv_items"] = dict(current, **wanted)
            if updates:
                self.admin.patch("/desks/" + self.desk_ids[name], updates, desk["_etag"])
                log("update", "desk", name, ", ".join(sorted(updates)))
            else:
                log("skip", "desk", name, "settings up to date")

    def ensure_workspaces(self):
        for name in data.WORKSPACES:
            if self.find_named("/workspaces", name, user=self.admin.user_id):
                log("skip", "workspace", name, "exists")
                continue
            self.admin.post("/workspaces", {"name": name, "user": self.admin.user_id})
            log("create", "workspace", name, "owned by admin")

    def ensure_personal_items(self):
        for spec in data.PERSONAL_ITEMS:
            item = self.get_item(spec["key"])
            if item is not None:
                log("skip", "personal", spec["slugline"], "exists ({})".format(item.get("state")))
                continue
            self.admin.post(
                "/archive",
                {
                    "guid": guid_for(spec["key"]),
                    "type": "text",
                    "language": "en",
                    "slugline": spec["slugline"],
                    "headline": spec["headline"],
                    "body_html": "<p>{}</p>".format(html_escape(spec["body"])),
                },
            )
            log("create", "personal", spec["slugline"], "admin's Personal space")

    def ensure_system_messages(self):
        # An active message is a toast at the top of every page, so it is only switched on on request.
        for spec in data.SYSTEM_MESSAGES:
            active = spec["is_active"] and self.args.system_message_on
            doc = self.find_named("/system_messages", spec["message_title"], field="message_title")
            if doc is None:
                self.admin.post("/system_messages", dict(spec, is_active=active))
                log("create", "message", spec["message_title"], "active" if active else "inactive")
            elif bool(doc.get("is_active")) != active:
                self.admin.patch("/system_messages/" + str(doc["_id"]), {"is_active": active}, doc["_etag"])
                log("update", "message", spec["message_title"], "active" if active else "inactive")
            else:
                log("skip", "message", spec["message_title"], "exists")

    def ensure_named(self, path, kind, specs):
        for spec in specs:
            if self.find_named(path, spec["name"]):
                log("skip", kind, spec["name"], "exists")
                continue
            self.admin.post(path, dict(spec))
            log("create", kind, spec["name"])

    def ensure_publishing(self):
        product_ids = {}
        for spec in data.PRODUCTS:
            doc = self.find_named("/products", spec["name"])
            if doc is None:
                doc = self.admin.post("/products", dict(spec))
                log("create", "product", spec["name"], spec["product_type"])
            else:
                log("skip", "product", spec["name"], "exists")
            product_ids[spec["name"]] = str(doc["_id"])

        spec = data.SNAPSHOT_SUBSCRIBER
        doc = self.find_named("/subscribers", spec["name"])
        if doc is None:
            log("warn", "subscr", spec["name"], "not in the snapshot")
        else:
            updates = {}
            for field in ("products", "api_products"):
                current = [str(p) for p in doc.get(field) or []]
                wanted = current + [product_ids[p] for p in spec[field] if product_ids[p] not in current]
                if wanted != current:
                    updates[field] = wanted
            if updates:
                self.admin.patch("/subscribers/" + str(doc["_id"]), updates, doc["_etag"])
                log("update", "subscr", spec["name"], "+ " + ", ".join(sorted(updates)))
            else:
                log("skip", "subscr", spec["name"], "products up to date")
            if spec.get("token_days"):
                tokens = self.admin.find_all("/subscriber_token", {"subscriber": str(doc["_id"])})
                if tokens:
                    log("skip", "token", spec["name"], "{} Content API token(s)".format(len(tokens)))
                else:
                    self.admin.post("/subscriber_token", {"subscriber": str(doc["_id"]), "expiry_days": spec["token_days"]})
                    log("create", "token", spec["name"], "Content API token, {} days".format(spec["token_days"]))

        for spec in data.SUBSCRIBERS:
            if self.find_named("/subscribers", spec["name"]):
                log("skip", "subscr", spec["name"], "exists")
                continue
            self.admin.post(
                "/subscribers",
                {
                    "name": spec["name"],
                    "email": spec["email"],
                    "subscriber_type": spec["subscriber_type"],
                    "sequence_num_settings": {"min": 1, "max": 9999},
                    "products": [product_ids[p] for p in spec["products"]],
                    "api_products": [product_ids[p] for p in spec["api_products"]],
                    "destinations": spec["destinations"],
                    "is_active": True,
                    "is_targetable": True,
                },
            )
            log("create", "subscr", spec["name"], "{} destination(s)".format(len(spec["destinations"])))

    def ensure_saved_searches(self):
        for name in data.SNAPSHOT_SAVED_SEARCHES_REMOVED:
            doc = self.find_named("/all_saved_searches", name)
            if doc is None:
                log("skip", "search", name, "absent")
                continue
            self.admin.delete("/saved_searches/" + str(doc["_id"]), doc["_etag"])
            log("delete", "search", name, "snapshot saved search")
        for spec in data.SAVED_SEARCHES:
            owner = self.client_for(spec["owner"])
            doc = self.find_named("/all_saved_searches", spec["name"], user=self.user_ids[spec["owner"]])
            if doc is None:
                doc = owner.post(
                    "/saved_searches",
                    {
                        "name": spec["name"],
                        "description": spec["description"],
                        "is_global": spec["is_global"],
                        "filter": {"query": {"q": spec["q"], "repo": spec["repo"]}},
                    },
                )
                log("create", "search", spec["name"], "{} by {}".format("global" if spec["is_global"] else "private", spec["owner"]))
            else:
                log("skip", "search", spec["name"], "exists")
            if spec.get("subscribe"):
                doc = owner.get("/saved_searches/" + str(doc["_id"]))
                uid = self.user_ids[spec["subscribe"]]
                subs = doc.get("subscribers") or {}
                if any(str(s.get("user")) == uid for s in subs.get("user_subscriptions") or []):
                    continue
                subscribers = {
                    "user_subscriptions": (subs.get("user_subscriptions") or []) + [{"user": uid, "scheduling": "0 8 * * *"}],
                    "desk_subscriptions": subs.get("desk_subscriptions") or [],
                }
                owner.patch("/saved_searches/" + str(doc["_id"]), {"subscribers": subscribers}, doc["_etag"])
                log("update", "search", spec["name"], "subscribed " + spec["subscribe"])

    def ensure_highlights(self):
        ids = {}
        for spec in data.HIGHLIGHTS:
            doc = self.find_named("/highlights", spec["name"])
            if doc is None:
                doc = self.admin.post(
                    "/highlights",
                    {"name": spec["name"], "desks": [self.desk_ids[d] for d in spec["desks"]],
                     "auto_insert": spec["auto_insert"], "groups": ["main"]},
                )
                log("create", "highlight", spec["name"], ", ".join(spec["desks"]))
            else:
                log("skip", "highlight", spec["name"], "exists")
            ids[spec["name"]] = str(doc["_id"])
        for key, names in data.HIGHLIGHT_MARKS.items():
            item = self.get_item(key)
            current = [str(h) for h in item.get("highlights") or []]
            missing = [ids[n] for n in names if ids[n] not in current]
            if not missing:
                log("skip", "hl-mark", item.get("slugline"), "marked")
                continue
            # The endpoint toggles each highlight it is given, so only send the missing ones.
            self.admin.post("/marked_for_highlights", {"highlights": missing, "marked_item": item["_id"]})
            log("mark", "hl-mark", item.get("slugline"), ", ".join(n for n in names if ids[n] in missing))

    def ensure_content_lists(self):
        list_ids = {}
        for spec in data.CONTENT_LISTS:
            doc = self.find_named("/content_lists", spec["name"])
            if doc is None:
                doc = self.admin.post(
                    "/content_lists",
                    {"name": spec["name"], "type": "manual", "limit": spec.get("limit"),
                     "description": spec.get("description"), "enabled": spec["enabled"]},
                )
                log("create", "list", spec["name"], "enabled" if spec["enabled"] else "disabled")
            list_id = str(doc["_id"])
            list_ids[spec["name"]] = list_id
            existing = self.admin.get("/content_lists/{}/items".format(list_id), max_results=200).get("_items", [])
            if existing:
                log("skip", "list", spec["name"], "{} item(s)".format(len(existing)))
                continue
            changes = [
                {"action": "add", "contentId": self.get_item(key)["_id"], "position": pos}
                for pos, key in enumerate(spec["items"])
            ]
            res = self.admin.request(
                "PATCH", "/content_lists/{}/items".format(list_id), payload={"updatedAt": None, "items": changes}
            )
            detail = "{} item(s)".format(len(changes))
            if spec.get("pinned"):
                self.admin.request(
                    "PATCH",
                    "/content_lists/{}/items".format(list_id),
                    payload={
                        "updatedAt": res.get("content_list_items_updated_at"),
                        "items": [{"action": "move", "contentId": self.get_item(spec["pinned"])["_id"],
                                   "position": 0, "sticky": True}],
                    },
                )
                detail += ", pinned " + self.get_item(spec["pinned"]).get("slugline")
            log("fill", "list", spec["name"], detail)
        for spec in data.CONTENT_LIST_WEBHOOKS:
            if self.find_named("/content_list_webhooks", spec["url"], field="url"):
                log("skip", "webhook", spec["url"], "exists")
                continue
            payload = dict(spec, excluded_lists=[list_ids[n] for n in spec.get("excluded_lists", [])])
            self.admin.post("/content_list_webhooks", payload)
            log("create", "webhook", spec["url"], "enabled" if spec["enabled"] else "disabled")

    def ensure_availability(self):
        spec = data.AVAILABILITY_TAGS
        if self.admin.get_optional("/vocabularies/" + spec["_id"]) is None:
            self.admin.post(
                "/vocabularies",
                {
                    "_id": spec["_id"],
                    "display_name": spec["display_name"],
                    "type": "manageable",
                    "selection_type": "multi selection",
                    "service": {"all": 1},
                    "unique_field": "qcode",
                    "schema": {"name": {"required": True}, "qcode": {"required": True}, "parent": {}},
                    "items": [dict(item, is_active=True) for item in spec["items"]],
                },
            )
            log("create", "vocab", spec["_id"], spec["display_name"])
        else:
            log("skip", "vocab", spec["_id"], "exists")

        for username, pattern in data.AVAILABILITY.items():
            tags = [{"code": t} for t in pattern["tags"]]
            working_days = {}
            for days, status, hours in pattern["days"]:
                if status == "partial":
                    entry = [{"start_time": hours[0], "end_time": hours[1], "tags": tags}]
                else:
                    entry = [{"tags": tags if status == "available" else []}]
                for day in days:
                    working_days[day] = {"status": status, "working_hours": entry}
            wanted = {"enabled": True, "language": [data.AVAILABILITY_LANGUAGE], "tags": tags, "working_days": working_days}
            uid = self.user_ids[username]
            doc = self.admin.get_optional("/default_user_availability/" + uid)
            if doc is not None and all(doc.get(k) == v for k, v in wanted.items()):
                log("skip", "avail", username, "default week set")
                continue
            self.admin.request(
                "PUT", "/default_user_availability/" + uid, payload=wanted, etag=doc["_etag"] if doc else None
            )
            log("update", "avail", username, "default week, 12 weeks generated")

        tz = schedule_tz()
        today = datetime.datetime.now(tz).date() if tz else utcnow().date()
        for override in data.AVAILABILITY_OVERRIDES:
            date = (today + datetime.timedelta(days=override["days"])).isoformat()
            uid = self.user_ids[override["user"]]
            entry = self.admin.find_one("/user_availability", {"user": uid, "date": date})
            if entry is None:
                log("warn", "avail", override["user"], "no entry for {}".format(date))
                continue
            if entry.get("status") == override["status"] and not entry.get("_generated", True):
                log("skip", "avail", override["user"], "{} already {}".format(date, override["status"]))
                continue
            self.admin.patch(
                "/user_availability/" + str(entry["_id"]),
                {"status": override["status"], "working_hours": [{"tags": []}]},
                entry["_etag"],
            )
            log("update", "avail", override["user"], "{} set to {} by admin".format(date, override["status"]))

    def ensure_comments(self):
        for spec in data.COMMENTS:
            item = self.get_item(spec["item"])
            existing = self.admin.find_all("/item_comments", {"item": item["_id"]})
            if any(c.get("text") == spec["text"] for c in existing):
                log("skip", "comment", item.get("slugline"), "by {}".format(spec["user"]))
                continue
            self.client_for(spec["user"]).post("/item_comments", {"item": item["_id"], "text": spec["text"]})
            log("create", "comment", item.get("slugline"), "by {}, mentions notify".format(spec["user"]))

    def run(self, picture_source):
        self.connect()
        self.load_reference_data()
        self.ensure_roles()
        self.ensure_categories()
        self.ensure_users()
        self.ensure_desks()
        self.ensure_default_desks()
        self.ensure_articles()
        self.ensure_pictures(picture_source)
        self.ensure_packages()
        self.ensure_marks()
        self.ensure_story_profile()
        self.ensure_custom_blocks()
        self.ensure_crop_sizes()
        self.ensure_body_media()
        self.ensure_dictionary()
        self.ensure_templates()
        self.ensure_recent_templates()
        self.ensure_desk_settings()
        self.ensure_workspaces()
        self.ensure_personal_items()
        self.ensure_system_messages()
        self.ensure_named("/auth_server_clients", "api key", data.API_KEYS)
        self.ensure_named("/ai_providers", "ai", data.AI_PROVIDERS)
        self.ensure_publishing()
        self.ensure_saved_searches()
        self.ensure_highlights()
        self.ensure_content_lists()
        self.ensure_availability()
        self.ensure_comments()
        self.ensure_locks()
        print("\nDone. Locks stay while the locking users' sessions are alive; run the script again to restore them.")

    # -- reset

    def try_delete(self, kind, name, path):
        doc = self.admin.get_optional(path)
        if doc is None:
            log("skip", kind, name, "absent")
            return
        try:
            self.admin.delete(path, doc["_etag"])
            log("delete", kind, name)
        except ApiError as err:
            if err.status >= 500:
                raise
            log("kept", kind, name, err.message)

    def reset_supporting_data(self):
        """Delete the named supporting documents; the rest of what run() changes needs a snapshot restore."""
        named = [
            ("/content_list_webhooks", "webhook", "url", [w["url"] for w in data.CONTENT_LIST_WEBHOOKS]),
            ("/content_lists", "list", "name", [c["name"] for c in data.CONTENT_LISTS]),
            ("/highlights", "highlight", "name", [h["name"] for h in data.HIGHLIGHTS]),
            ("/all_saved_searches", "search", "name", [s["name"] for s in data.SAVED_SEARCHES]),
            ("/system_messages", "message", "message_title", [m["message_title"] for m in data.SYSTEM_MESSAGES]),
            ("/auth_server_clients", "api key", "name", [k["name"] for k in data.API_KEYS]),
            ("/ai_providers", "ai", "name", [p["name"] for p in data.AI_PROVIDERS]),
            ("/workspaces", "workspace", "name", list(data.WORKSPACES)),
        ]
        for path, kind, field, values in named:
            for value in values:
                doc = self.find_named(path, value, field=field)
                if doc is None:
                    log("skip", kind, value, "absent")
                    continue
                item_path_ = "/saved_searches" if path == "/all_saved_searches" else path
                try:
                    self.admin.delete("{}/{}".format(item_path_, doc["_id"]), doc["_etag"])
                    log("delete", kind, value)
                except ApiError as err:
                    if err.status >= 500:
                        raise
                    log("kept", kind, value, err.message)
        log("kept", "settings", "profile, templates, vocabularies, dictionary, subscribers, availability",
            "restore the snapshot to undo these")

    def reset(self):
        self.connect()
        self.reset_supporting_data()
        seed_desk_names = {d["name"] for d in all_desks(self.args.send_and_duplicate_desk) if not d.get("snapshot")}

        specs = [("package", s) for s in data.PACKAGES]
        specs += [("article", s) for s in data.ARTICLES] + [("picture", s) for s in data.PICTURES]
        for kind, spec in specs:
            item = self.get_item(spec["key"])
            label = spec["slugline"] if kind != "picture" else spec["headline"]
            if item is None:
                log("skip", kind, label, "absent")
                continue
            if item.get("lock_user"):
                self.admin.post(item_path(item["_id"], "unlock"), {})
                item = self.admin.get(item_path(item["_id"]))
                log("unlock", kind, label)
            state = item.get("state")
            if item.get("marked_for_user") and state not in PUBLISHED_STATES | {"spiked", "scheduled"}:
                self.admin.patch(item_path(item["_id"]), {"marked_for_user": None}, item["_etag"])
                item = self.admin.get(item_path(item["_id"]))
                log("unmark", kind, label)
            if state == "scheduled":
                self.admin.patch(item_path(item["_id"]), {"publish_schedule": None}, item["_etag"])
                item = self.admin.get(item_path(item["_id"]))
                state = item.get("state")
                log("unsched", kind, label)
            if state in PUBLISHED_STATES:
                log("kept", kind, label, "{} items cannot be removed through the API".format(state))
            elif state == "spiked":
                log("skip", kind, label, "already spiked")
            else:
                self.admin.patch(item_path(item["_id"], "spike"), {"state": "spiked"}, item["_etag"])
                log("spike", kind, label)

        # Users: clear the default desk first, a desk that is someone's default cannot be deleted.
        desk_docs = {}
        for spec in all_desks(self.args.send_and_duplicate_desk):
            doc = self.admin.find_one("/desks", {"name": spec["name"]})
            if doc:
                desk_docs[spec["name"]] = doc
        seed_desk_ids = {str(desk_docs[n]["_id"]) for n in seed_desk_names if n in desk_docs}

        admin_doc = self.find_user("admin")
        if admin_doc and str(admin_doc.get("desk") or "") in seed_desk_ids:
            fallback = self.admin.find_one("/desks", {"name": "Sports"})
            self.admin.patch(
                "/users/" + str(admin_doc["_id"]), {"desk": str(fallback["_id"]) if fallback else None}, admin_doc["_etag"]
            )
            log("update", "user", self.args.user, "default desk Sports")

        seed_user_ids = set()
        for spec in data.USERS:
            doc = self.find_user(spec["username"])
            if doc is None:
                log("skip", "user", spec["username"], "absent")
                continue
            seed_user_ids.add(str(doc["_id"]))
            if doc.get("desk"):
                self.admin.patch("/users/" + str(doc["_id"]), {"desk": None}, doc["_etag"])
                doc = self.admin.get("/users/" + str(doc["_id"]))
            if doc.get("is_enabled", True) or doc.get("is_active", True):
                self.admin.delete("/users/" + str(doc["_id"]), doc["_etag"])
                log("disable", "user", spec["username"], "Superdesk only soft-deletes users")
            else:
                log("skip", "user", spec["username"], "already disabled")

        for spec in all_desks(self.args.send_and_duplicate_desk):
            doc = desk_docs.get(spec["name"])
            if doc is None:
                log("skip", "desk", spec["name"], "absent")
                continue
            if spec.get("snapshot"):
                updates = {}
                members = [str(m["user"]) for m in doc.get("members") or []]
                kept = [uid for uid in members if uid not in seed_user_ids]
                if kept != members:
                    updates["members"] = [{"user": uid} for uid in kept]
                if spec.get("monitoring") and doc.get("monitoring_settings"):
                    updates["monitoring_settings"] = []
                if updates:
                    self.admin.patch("/desks/" + str(doc["_id"]), updates, doc["_etag"])
                    log("update", "desk", spec["name"], "removed " + ", ".join(sorted(updates)))
                else:
                    log("skip", "desk", spec["name"], "nothing to revert")
            else:
                self.try_delete("desk", spec["name"], "/desks/" + str(doc["_id"]))

        for spec in data.ROLES:
            if spec.get("snapshot"):
                continue
            doc = self.admin.find_one("/roles", {"name": spec["name"]})
            if doc is None:
                log("skip", "role", spec["name"], "absent")
                continue
            self.try_delete("role", spec["name"], "/roles/" + str(doc["_id"]))

        voc = self.admin.get_optional("/vocabularies/categories")
        if voc is not None:
            ours = {c["qcode"] for c in data.CATEGORIES}
            items = []
            for item in voc.get("items", []):
                if item.get("qcode") in ours:
                    continue
                if item.get("qcode") in data.HIDDEN_CATEGORY_QCODES:
                    item = dict(item, is_active=True)
                items.append(item)
            if items != voc.get("items", []):
                self.admin.patch("/vocabularies/categories", {"items": items}, voc["_etag"])
                log("update", "vocab", "categories", "restored")
            else:
                log("skip", "vocab", "categories", "nothing to revert")

        print(
            "\nDone. For a complete reset, restore the e2e snapshot instead:\n"
            "  curl -X POST {}/restore_record -H 'Content-Type: application/json' -d '{{\"name\": \"main\"}}'".format(
                self.api_url
            )
        )


# ---- dry run ----------------------------------------------------------------------------------------


def print_plan(args, picture_source):
    users_by_name = {u["username"]: u for u in data.USERS}
    desks = all_desks(args.send_and_duplicate_desk)
    tz = data.NEWSROOM["timezone"] if schedule_tz() else "UTC (zoneinfo unavailable)"
    print("Dry run, no requests sent. Target: {}\n".format(args.api_url))

    if args.reset:
        print("Reset plan (best effort, the API cannot delete everything):")
        print("  - unlock, unmark and deschedule seeded items, then spike every unpublished one")
        print("  - published items stay: Superdesk has no API to remove them")
        print("  - clear default desks and disable users: {}".format(", ".join(users_by_name)))
        print("  - delete desks {} (refused by the server while they hold items)".format(
            ", ".join(d["name"] for d in desks if not d.get("snapshot"))))
        print("  - remove seeded members and monitoring groups from {}".format(
            ", ".join(d["name"] for d in desks if d.get("snapshot"))))
        print("  - delete roles {} (refused while users still have them)".format(
            ", ".join(r["name"] for r in data.ROLES if not r.get("snapshot"))))
        print("  - delete seeded content lists and webhooks, highlights, saved searches, system messages, API keys, "
              "AI providers and workspaces; profile, template, vocabulary, dictionary, subscriber and availability "
              "changes stay (restore the snapshot)")
        print("  - categories vocabulary: remove {} and re-activate {}".format(
            ", ".join(c["qcode"] for c in data.CATEGORIES), ", ".join(data.HIDDEN_CATEGORY_QCODES)))
        return

    print("Roles:")
    for role in data.ROLES:
        note = "only if missing (exists in the e2e snapshot)" if role.get("snapshot") else "create if missing"
        print("  {:<12} {} privileges, {}".format(role["name"], len(role["privileges"]), note))

    print("\nCategories vocabulary: {}; hide {}".format(
        ", ".join("{} ({})".format(c["name"], c["qcode"]) for c in data.CATEGORIES),
        ", ".join(data.HIDDEN_CATEGORY_QCODES)))

    print("\nUsers (password = username):")
    for user in data.USERS:
        print("  {:<13} {:<16} {:<11} {:<30} default desk {}".format(
            user["username"], display_name(user["username"], users_by_name), user["role"], user["job_title"],
            user.get("default_desk")))
    print("  admin default desk: {}".format(data.ADMIN_DEFAULT_DESK))

    print("\nDesks:")
    for desk in desks:
        kind = "existing snapshot desk, add members" if desk.get("snapshot") else desk.get("desk_type", "production")
        print("  {} ({})".format(desk["name"], kind))
        print("    stages:  {}".format(", ".join(s["name"] for s in desk["stages"])))
        print("    members: {}".format(", ".join(desk.get("members", []))))
        if desk.get("monitoring"):
            print("    monitoring groups: stages, desk output, scheduled desk output")

    print("\nArticles ({}):".format(len(data.ARTICLES)))
    for art in data.ARTICLES:
        action = art.get("action") or "on stage"
        extra = []
        if art.get("publish_at"):
            extra.append("at " + wall_time(art["publish_at"])[:16].replace("T", " "))
        if art.get("embargo"):
            extra.append("embargo " + wall_time(art["embargo"])[:16].replace("T", " "))
        print("  {:<9} {:<17} {:<20} u{} p{} {:<13} {:<9} {}".format(
            art["desk"], art["stage"], art["slugline"], art["urgency"], art["priority"], art["author"], action,
            " ".join(extra)))
        print("            {}".format(art["headline"]))
    if any(a.get("publish_at") or a.get("embargo") for a in data.ARTICLES):
        print("  (schedule and embargo times are wall-clock times in {})".format(tz))

    print("\nPictures ({}): {}".format(len(data.PICTURES), picture_source.describe()))
    for pic in data.PICTURES:
        print("  {} / {}  {}  by {}".format(pic["desk"], pic["stage"], pic["headline"], pic["author"]))

    print("\nPackages:")
    for pkg in data.PACKAGES:
        print("  {} / {}  {}  {}  items: {}".format(
            pkg["desk"], pkg["stage"], pkg["slugline"], pkg["headline"], ", ".join(pkg["items"])))

    articles = {a["key"]: a for a in data.ARTICLES}
    print("\nMarked for user:")
    for mark in data.MARKS:
        print("  {:<20} for {}".format(articles[mark["item"]]["slugline"], mark["user"]))
    print("\nLocked (open for editing):")
    for lock in data.LOCKS:
        print("  {:<20} by {}".format(articles[lock["item"]]["slugline"], lock["user"]))

    print("\nSettings and supporting data:")
    print("  Story profile body: {} formatting options, maxlength {}".format(
        len(data.STORY_BODY["format_options"]), data.STORY_BODY["maxlength"]))
    print("  custom blocks: {}".format(", ".join(b["display_name"] for b in data.CUSTOM_BLOCKS)))
    print("  crop sizes: add {}".format(", ".join(c["name"] for c in data.CROP_SIZES)))
    print("  picture {} in the body of {}".format(data.BODY_MEDIA["picture"], data.BODY_MEDIA["item"]))
    print("  dictionary {} ({}): {} words".format(
        data.DICTIONARY["name"], data.DICTIONARY["language_id"], len(dictionary_words(data.DICTIONARY.get("system_words")))))
    print("  templates: {}".format(", ".join("{} -> {}".format(t["template_name"], t["headline"]) for t in data.TEMPLATES)))
    for name, spec in data.DESK_SETTINGS.items():
        print("  desk {}: {}".format(name, ", ".join("{} {}".format(k, v) for k, v in spec.items())))
    print("  workspaces: {}".format(", ".join(data.WORKSPACES)))
    print("  personal items: {}".format(", ".join(p["slugline"] for p in data.PERSONAL_ITEMS)))
    print("  system messages: {}".format(", ".join(
        "{} ({})".format(m["message_title"], "active" if m["is_active"] and args.system_message_on else "inactive")
        for m in data.SYSTEM_MESSAGES)))
    print("  API keys: {}".format(", ".join(k["name"] for k in data.API_KEYS)))
    print("  AI providers: {}".format(", ".join(p["name"] for p in data.AI_PROVIDERS)))
    print("  products: {}; subscribers: {} (+ {} gets {})".format(
        ", ".join(p["name"] for p in data.PRODUCTS), ", ".join(s["name"] for s in data.SUBSCRIBERS),
        data.SNAPSHOT_SUBSCRIBER["name"], ", ".join(data.SNAPSHOT_SUBSCRIBER["products"])))
    print("  saved searches: {}; remove {}".format(", ".join(
        "{} ({}, {})".format(s["name"], "global" if s["is_global"] else "private", s["owner"]) for s in data.SAVED_SEARCHES),
        ", ".join(data.SNAPSHOT_SAVED_SEARCHES_REMOVED)))
    print("  highlights: {}; marks: {}".format(", ".join(h["name"] for h in data.HIGHLIGHTS), ", ".join(
        "{} ({})".format(articles[k]["slugline"], ", ".join(v)) for k, v in data.HIGHLIGHT_MARKS.items())))
    for c in data.CONTENT_LISTS:
        print("  content list {}: {} item(s){}{}".format(
            c["name"], len(c["items"]), ", limit {}".format(c["limit"]) if c.get("limit") else "",
            "" if c["enabled"] else ", disabled"))
    print("  content list webhooks: {}".format(", ".join(w["url"] for w in data.CONTENT_LIST_WEBHOOKS)))
    print("  availability: vocabulary {}, default weeks for {}, overrides {}".format(
        data.AVAILABILITY_TAGS["_id"], ", ".join(data.AVAILABILITY),
        ", ".join("{} +{}d {}".format(o["user"], o["days"], o["status"]) for o in data.AVAILABILITY_OVERRIDES)))
    for c in data.COMMENTS:
        print("  comment on {} by {}: {}".format(articles[c["item"]]["slugline"], c["user"], c["text"]))


# ---- main -------------------------------------------------------------------------------------------


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Seed a Superdesk e2e instance with a fictional newsroom.")
    parser.add_argument("--api-url", default="http://localhost:5002/api", help="Superdesk API base URL")
    parser.add_argument("--user", default="admin", help="administrator username (default: admin)")
    parser.add_argument("--password", default="admin", help="administrator password (default: admin)")
    parser.add_argument("--dry-run", action="store_true", help="print the plan without connecting to the server")
    parser.add_argument("--reset", action="store_true", help="remove what this script created, where the API allows")
    parser.add_argument("--images-dir", help="use .jpg/.png files from this folder for the picture items")
    parser.add_argument(
        "--send-and-duplicate-desk",
        action="store_true",
        help="also create the 'Test' desk with a 'Working' stage named by the host client config",
    )
    parser.add_argument(
        "--system-message-on",
        action="store_true",
        help="activate the system message flagged is_active in seed_data.py (a toast on every page); "
        "without it every seeded system message is left inactive",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        validate_data()
        source = PictureSource(args.images_dir)
        if args.dry_run:
            print_plan(args, source)
            return 0
        seeder = Seeder(args)
        if args.reset:
            seeder.reset()
        else:
            seeder.run(source)
        return 0
    except ApiError as err:
        print("\nERROR: the server rejected a request\n{}".format(err), file=sys.stderr)
        return 1
    except SeedError as err:
        print("\nERROR: {}".format(err), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
