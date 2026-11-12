#!/usr/bin/env python3
"""Seed the Broadcasting module (shows and rundowns) for the broadcasting-shows-and-rundowns screenshots.

Creates the four vocabularies rundown items use (item types, subitem types, statuses, cameras), two shows of the
fictional Meridian News Service, one rundown template per show (the evening one creates rundowns automatically on
weekdays) and three rundowns made from those templates. Today's evening rundown gets a full running order with
every item type, statuses, cameras, subitems and scripts, so the rundown list, the rundown editor, the template
manager, the item editor, search and export all have realistic content.

Needs a server with `apps.rundowns` in INSTALLED_APPS and a client that loads the `broadcasting` extension
(CAPTURE.md, "Broadcasting on the e2e stack"). When the server has no `/api/shows`, the script says so and exits
without changes. Run it after seed.py; it does not depend on anything seed.py creates.

Dates are Europe/London dates (the e2e server's DEFAULT_TIMEZONE, which RUNDOWNS_TIMEZONE defaults to) relative to
the day the script runs. Standard library only. See SEED.md.

    python3 seed_broadcasting.py --api-url http://localhost:5011/api [--dry-run]
"""

import argparse
import datetime
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from seed import ApiError, SeedError, log, login  # noqa: E402

from zoneinfo import ZoneInfo  # noqa: E402

TZ_NAME = "Europe/London"
TZ = ZoneInfo(TZ_NAME)

# Python strftime format of the generated rundown names. It has to be one of the formats the template editor offers,
# which are built from the client's `view.dateformat` (DD/MM/YYYY on the e2e client): otherwise the editor's date
# format dropdown shows a value it does not list.
TITLE_DATE_FORMAT = "%d/%m/%Y"

VOCAB_SCHEMA_COLOR = {
    "name": {"translate": True},
    "qcode": {"type": "string"},
    "color": {"type": "color", "label": "Color"},
}

# The server builds a different technical title for the item type codes PRLG and AACC (type name, show code and
# title joined with dashes); avoid them so every row reads as its title.
VOCABULARIES = [
    {
        "_id": "rundown_item_types",
        "display_name": "Item Type",
        "schema": VOCAB_SCHEMA_COLOR,
        "items": [
            {"name": "Intro", "qcode": "INTRO", "color": "#1d6fbf"},
            {"name": "Report", "qcode": "REPORT", "color": "#36b37e"},
            {"name": "Live", "qcode": "LIVE", "color": "#de350b"},
            {"name": "Interview", "qcode": "INTERVIEW", "color": "#6554c0"},
            {"name": "Weather", "qcode": "WEATHER", "color": "#00a3bf"},
            {"name": "Outro", "qcode": "OUTRO", "color": "#5e6c84"},
        ],
    },
    {
        "_id": "rundown_subitem_types",
        "display_name": "Subitem Type",
        "schema": VOCAB_SCHEMA_COLOR,
        "items": [
            {"name": "Graphics", "qcode": "GRAF", "color": "#ff991f"},
            {"name": "Lower third", "qcode": "LTHIRD", "color": "#00875a"},
            {"name": "Video wall", "qcode": "WALL", "color": "#403294"},
        ],
    },
    {
        "_id": "rundown_item_status",
        "display_name": "Rundown Item Status",
        "schema": VOCAB_SCHEMA_COLOR,
        "items": [
            {"name": "pending", "qcode": "pending", "color": "#ff5630"},
            {"name": "in approval", "qcode": "in-approval", "color": "#ff991f"},
            {"name": "approved", "qcode": "approved", "color": "#36b37e"},
        ],
    },
    {
        "_id": "camera",
        "display_name": "Camera",
        "schema": {"name": {"type": "string"}, "qcode": {"type": "string"}},
        "items": [
            {"name": "K1", "qcode": "K1"},
            {"name": "K2", "qcode": "K2"},
            {"name": "K3", "qcode": "K3"},
        ],
    },
]

SHOWS = [
    {"title": "Meridian Tonight", "shortcode": "MT", "description": "Evening news bulletin", "planned_duration": 1800},
    {"title": "Morning Briefing", "shortcode": "MB", "description": "Weekday headlines and markets before nine",
     "planned_duration": 900},
]


def p(*paragraphs):
    return "".join("<p>{}</p>".format(text) for text in paragraphs)


# Template items are copied into every rundown created from the template (type, title, content, subitems and
# durations; not cameras or status).
TEMPLATES = [
    {
        "show": "Meridian Tonight",
        "title": "Weeknight edition",
        "airtime_time": "19:00:00",
        "planned_duration": 1800,
        "title_template": {"prefix": "Meridian Tonight", "separator": "//", "date_format": TITLE_DATE_FORMAT},
        # Weekly, created 12 hours before air time. `by_day` holds what the template editor stores when Mon to Fri
        # are picked: the client numbers days from Sunday (0) while the server's rrule reads 0 as Monday, so the
        # server would create these rundowns Tuesday to Saturday. The client's own default, [0, 1, 2, 3, 4], shows
        # Sun to Thu selected. Left as the UI shows it, since the screenshot documents the editor.
        "repeat": True,
        "schedule": {"freq": "WEEKLY", "interval": 1, "by_day": [1, 2, 3, 4, 5]},
        "autocreate_before_seconds": 43200,
        "items": [
            {"item_type": "INTRO", "title": "Opening headlines", "planned_duration": 60, "duration": 60,
             "content": p("Good evening. Tonight on Meridian Tonight: the three main parties set out their "
                          "promises, the Bank of Aldmark holds rates, and Arlenport council votes on the tram "
                          "extension.")},
            {"item_type": "WEATHER", "title": "Weather", "planned_duration": 90, "duration": 90,
             "content": p("Showers clearing from the west overnight, a bright but cold start tomorrow."),
             "subitems": [{"qcode": "WALL", "technical_info": "Weather map, national", "content": ""}]},
            {"item_type": "OUTRO", "title": "Closing", "planned_duration": 30, "duration": 30,
             "content": p("That is Meridian Tonight. The Morning Briefing is on at seven. Good night.")},
        ],
    },
    {
        "show": "Morning Briefing",
        "title": "Weekday morning",
        "airtime_time": "07:00:00",
        "planned_duration": 900,
        "title_template": {"prefix": "Morning Briefing", "separator": "//", "date_format": TITLE_DATE_FORMAT},
        "repeat": False,
        "schedule": None,
        "items": [
            {"item_type": "INTRO", "title": "Headlines", "planned_duration": 60, "duration": 60,
             "content": p("Good morning, this is the Morning Briefing.")},
            {"item_type": "REPORT", "title": "Markets at the open", "planned_duration": 120, "duration": 120,
             "content": p("Bond yields edge higher in early trading in Arlenport.")},
            {"item_type": "WEATHER", "title": "Weather and travel", "planned_duration": 60, "duration": 60,
             "content": p("Fog on the coast road, ferries running to timetable.")},
        ],
    },
]

# Rundowns are created through POST /rundowns from their template, like the Create rundown dialog does, and listed
# on the Broadcasting page in this order (most recently changed first). `days` is relative to today. Without `items` the rundown keeps the items copied from its template.
# With `items`, the list is the full running order: an entry whose title matches a template item updates that
# item (status, camera), any other entry is created, and the rundown's item order is set to this list.
# The created rundowns stay unlocked.
RUNDOWNS = [
    {
        "template": "Weeknight edition",
        "days": 0,
        "items": [
            {"title": "Opening headlines", "status": "approved", "camera": ["K1"]},
            {
                "item_type": "REPORT", "title": "Election debate: what each party promised",
                "planned_duration": 210, "duration": 240, "status": "approved", "camera": ["K2"],
                "content": p(
                    "The leaders of the three main parties met in Arlenport tonight for the first of three televised "
                    "debates before polling day.",
                    "The coalition promised tax relief for 1.2 million households. The Civic Union said it would "
                    "pay for more social housing with a levy on holiday rentals.",
                    "Our political editor Maren Holt has the main promises and what they would cost.",
                ),
                "subitems": [
                    {"qcode": "GRAF", "technical_info": "Poll chart, full screen",
                     "content": p("Latest poll: Coalition 34, Civic Union 30, Greens 12.")},
                    {"qcode": "LTHIRD", "technical_info": "Maren Holt, Political Editor", "content": ""},
                ],
                "additional_notes": "Package ends on a two-shot of the leaders.",
            },
            {
                "item_type": "INTERVIEW", "title": "Interview: Finance Minister Ilse Marrow",
                "planned_duration": 360, "duration": 330, "status": "in-approval", "camera": ["K1", "K2"],
                "content": p(
                    "The Finance Minister joins us in the studio to explain how the government will pay for its "
                    "tax cuts.",
                    "Questions: the short-term rental levy, the freeze on defence spending, the bond market.",
                ),
                "subitems": [
                    {"qcode": "LTHIRD", "technical_info": "Ilse Marrow, Finance Minister", "content": ""},
                ],
            },
            {
                "item_type": "REPORT", "title": "Bank of Aldmark holds key rate",
                "planned_duration": 150, "duration": 150, "status": "in-approval",
                "content": p("The Bank of Aldmark kept its key rate at 3.25 percent for a fourth meeting."),
                "subitems": [{"qcode": "GRAF", "technical_info": "Rate chart, five years", "content": ""}],
            },
            {
                "item_type": "LIVE", "title": "Live from Arlenport City Hall",
                "planned_duration": 240, "duration": 300, "status": "pending", "camera": ["K3"],
                "content": p("Councillors are still debating the tram extension to the eastern suburbs. "
                             "Our reporter is outside the chamber."),
                "subitems": [{"qcode": "WALL", "technical_info": "City Hall live feed", "content": ""}],
            },
            {
                "item_type": "REPORT", "title": "Saltmere port expansion approved",
                "planned_duration": 120, "duration": 120, "status": "approved",
                "content": p("The expansion of Saltmere port won environmental approval this afternoon."),
            },
            {
                "item_type": "REPORT", "title": "Arlenport Marathon preview",
                "planned_duration": 120, "duration": 120, "status": "in-approval",
                "content": p("The course record is under threat on Sunday, with three past winners on the start "
                             "line."),
            },
            {"title": "Weather", "status": "approved", "camera": ["K1"]},
            {"title": "Closing", "status": "approved", "camera": ["K1"]},
        ],
    },
    {"template": "Weekday morning", "days": 0},
    {"template": "Weeknight edition", "days": -1},
    {"template": "Weekday morning", "days": -1},
    {"template": "Weeknight edition", "days": -2},
    {"template": "Weekday morning", "days": -2},
    {"template": "Weeknight edition", "days": -5},
]

ITEM_FIELDS = ("item_type", "title", "planned_duration", "duration", "content", "subitems", "additional_notes",
               "status", "camera")


def local_date(days):
    return datetime.datetime.now(TZ).date() + datetime.timedelta(days=days)


def rundown_title(template, date):
    tt = template["title_template"]
    return "{} {} {}".format(tt["prefix"], tt["separator"], date.strftime(tt["date_format"]))


def template_by_title(title):
    return next(t for t in TEMPLATES if t["title"] == title)


class Seeder:
    def __init__(self, client):
        self.c = client
        self.shows = {}
        self.templates = {}

    def all(self, path):
        # rundowns and rundown_items are searched in Elasticsearch, where a Mongo-style `where` fails with HTTP 500.
        return self.c.get(path, max_results=200)["_items"]

    def available(self):
        try:
            self.c.get("/shows", max_results=1)
        except ApiError as err:
            if err.status == 404:
                return False
            raise
        return True

    def seed_vocabularies(self):
        for spec in VOCABULARIES:
            items = [dict(item, is_active=True) for item in spec["items"]]
            voc = self.c.get_optional("/vocabularies/" + spec["_id"])
            if voc is None:
                self.c.post("/vocabularies", {
                    "_id": spec["_id"],
                    "display_name": spec["display_name"],
                    "type": "manageable",
                    "unique_field": "qcode",
                    "selection_type": "do not show",
                    "schema": spec["schema"],
                    "items": items,
                })
                log("create", "vocab", spec["_id"], ", ".join(i["name"] for i in items))
                continue
            # The server drops `is_active` from stored items, so compare without it.
            current = [{k: i[k] for k in ("name", "qcode", "color") if k in i} for i in voc.get("items", [])]
            if current == spec["items"] and voc.get("display_name") == spec["display_name"]:
                log("skip", "vocab", spec["_id"])
                continue
            self.c.patch("/vocabularies/" + spec["_id"],
                         {"items": items, "display_name": spec["display_name"], "schema": spec["schema"]},
                         voc["_etag"])
            log("update", "vocab", spec["_id"], ", ".join(i["name"] for i in items))

    def seed_shows(self):
        existing = {s["title"]: s for s in self.c.get("/shows", max_results=200)["_items"]}
        for spec in SHOWS:
            show = existing.get(spec["title"])
            if show is None:
                show = self.c.post("/shows", spec)
                log("create", "show", spec["title"])
            else:
                changes = {k: v for k, v in spec.items() if show.get(k) != v}
                if changes:
                    show.update(self.c.patch("/shows/" + show["_id"], changes, show["_etag"]))
                    log("update", "show", spec["title"], ", ".join(sorted(changes)))
                else:
                    log("skip", "show", spec["title"])
            self.shows[spec["title"]] = show

    def seed_templates(self):
        for spec in TEMPLATES:
            show_id = self.shows[spec["show"]]["_id"]
            path = "/shows/{}/templates".format(show_id)
            existing = {t["title"]: t for t in self.c.get(path, max_results=200)["_items"]}
            payload = {k: v for k, v in spec.items() if k != "show"}
            payload["show"] = show_id
            # The air date is where automatic creation starts; the editor shows it next to the air time.
            payload["airtime_date"] = local_date(0).isoformat()
            template = existing.get(spec["title"])
            if template is None:
                template = self.c.post(path, payload)
                log("create", "template", spec["title"], "for " + spec["show"])
            else:
                changes = {k: v for k, v in payload.items()
                           if k not in ("items", "airtime_date", "show") and template.get(k) != v}
                if changes:
                    template = self.c.patch("{}/{}".format(path, template["_id"]), changes, template["_etag"])
                    log("update", "template", spec["title"], ", ".join(sorted(changes)))
                else:
                    log("skip", "template", spec["title"])
            self.templates[spec["title"]] = template

    def rundown_items(self, rundown):
        ids = [ref["_id"] for ref in rundown.get("items") or []]
        if not ids:
            return []
        return [item for item in (self.c.get_optional("/rundown_items/" + i) for i in ids) if item is not None]

    def seed_rundowns(self):
        ids = []
        for spec in reversed(RUNDOWNS):
            template_spec = template_by_title(spec["template"])
            template = self.templates[spec["template"]]
            show_id = self.shows[template_spec["show"]]["_id"]
            date = local_date(spec["days"])
            title = rundown_title(template_spec, date)
            rundown = next((r for r in self.all("/rundowns") if r["show"] == show_id and r["title"] == title), None)
            if rundown is None:
                created = self.c.post("/rundowns", {
                    "show": show_id, "template": template["_id"], "airtime_date": date.isoformat(), "title": title,
                })
                rundown = self.c.get("/rundowns/" + created["_id"])
                log("create", "rundown", title)
            else:
                log("skip", "rundown", title)
            if spec.get("items"):
                self.seed_running_order(rundown, spec["items"])
            ids.insert(0, rundown["_id"])
        self.order_rundowns(ids)

    def order_rundowns(self, ids):
        """The page lists rundowns by `_updated`, newest first, and opening, locking or unlocking a rundown changes
        it. Touch the rundowns oldest first so the list starts in RUNDOWNS order again."""
        listed = [r["_id"] for r in self.c.get("/rundowns", max_results=200, sort='[("_updated", -1)]')["_items"]]
        if [i for i in listed if i in ids] == ids:
            log("skip", "order", "rundown list")
            return
        for rundown_id in reversed(ids):
            rundown = self.c.get("/rundowns/" + rundown_id)
            self.c.patch("/rundowns/" + rundown_id, {"title": rundown["title"]}, rundown["_etag"])
            time.sleep(1.1)  # `_updated` has a resolution of one second
        log("update", "order", "rundown list", "{} rundowns".format(len(ids)))

    def seed_running_order(self, rundown, specs):
        items = {i["title"]: i for i in self.rundown_items(rundown)}
        order = []
        for spec in specs:
            item = items.get(spec["title"])
            if item is None:
                payload = {k: spec[k] for k in ITEM_FIELDS if k in spec}
                payload["rundown"] = rundown["_id"]
                item = self.c.post("/rundown_items", payload)
                log("create", "item", spec["title"])
            else:
                changes = {k: spec[k] for k in ITEM_FIELDS if k in spec and item.get(k) != spec[k]}
                if changes:
                    item.update(self.c.patch("/rundown_items/" + item["_id"], changes, item["_etag"]))
                    log("update", "item", spec["title"], ", ".join(sorted(changes)))
                else:
                    log("skip", "item", spec["title"])
            order.append(item["_id"])
        rundown = self.c.get("/rundowns/" + rundown["_id"])
        if [ref["_id"] for ref in rundown.get("items") or []] != order:
            self.c.patch("/rundowns/" + rundown["_id"], {"items": [{"_id": i} for i in order]}, rundown["_etag"])
            log("update", "rundown", rundown["title"], "running order, {} items".format(len(order)))

    def unlock_all(self):
        """Release locks left by a capture that did not close a rundown or an item. A lock belongs to the session
        that took it, so the seed takes it over (`force-lock`, what the Unlock button does) and then releases it."""
        for resource in ("rundowns", "rundown_items"):
            for doc in (d for d in self.all("/" + resource) if d.get("_lock")):
                path = "/{}/{}".format(resource, doc["_id"])
                try:
                    locked = self.c.patch(path, {"_lock_action": "force-lock"}, doc["_etag"])
                    self.c.patch(path, {"_lock_action": "unlock"}, locked["_etag"])
                    log("unlock", resource[:-1], doc.get("title", doc["_id"]))
                except ApiError as err:
                    log("keep", resource[:-1], doc.get("title", doc["_id"]), "unlock refused: " + err.message)

    def run(self):
        if not self.available():
            log("skip", "module", "broadcasting", "the server has no /api/shows (apps.rundowns not installed)")
            return
        self.seed_vocabularies()
        self.seed_shows()
        self.seed_templates()
        self.unlock_all()
        self.seed_rundowns()


def print_plan(args):
    print("API: {}  user: {}".format(args.api_url, args.user))
    print("today in {}: {}".format(TZ_NAME, local_date(0)))
    for spec in VOCABULARIES:
        print("vocab    {:<22} {}".format(spec["_id"], ", ".join(i["name"] for i in spec["items"])))
    for spec in SHOWS:
        print("show     {:<22} {} {}s".format(spec["title"], spec["shortcode"], spec["planned_duration"]))
    for spec in TEMPLATES:
        print("template {:<22} {} at {}, {} items, {}".format(
            spec["title"], spec["show"], spec["airtime_time"], len(spec["items"]),
            "weekdays" if spec["schedule"] else "no schedule"))
    for spec in RUNDOWNS:
        template = template_by_title(spec["template"])
        items = spec.get("items") or template["items"]
        print("rundown  {:<36} {} items".format(rundown_title(template, local_date(spec["days"])), len(items)))


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Seed shows, rundown templates and rundowns for the Broadcasting "
                                                 "screenshots.")
    parser.add_argument("--api-url", default="http://localhost:5011/api", help="API base URL")
    parser.add_argument("--user", default="admin", help="administrator username (default: admin)")
    parser.add_argument("--password", default="admin", help="administrator password (default: admin)")
    parser.add_argument("--dry-run", action="store_true", help="print the plan without connecting to the server")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.dry_run:
        print_plan(args)
        return 0
    try:
        Seeder(login(args.api_url, args.user, args.password)).run()
    except SeedError as err:
        print("error: {}".format(err), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
