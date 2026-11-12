#!/usr/bin/env python3
"""Seed the superdesk-planning e2e stack with a small newsroom for the Planning documentation screenshots.

Creates what the planning manifests (superdesk-planning-component.json, planning-administration.json) and the
Master Desk Assignments tab need: desks named like the rest of the guide, fictional user names, events,
planning items with coverages, assignments in the states assigned / in progress / completed on five desks,
agendas, event templates, a saved filter, custom layouts, locations and the vocabularies they use.

Times are Sydney wall-clock times (the e2e server's DEFAULT_TIMEZONE) relative to the day the script runs.
Standard library only. See SEED.md.

    python3 seed_planning.py --api-url http://localhost:5021/api [--reset] [--scenario NAME] [--dry-run]
"""

import argparse
import datetime
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from seed import ApiError, Client, SeedError, log, login  # noqa: E402
import seed_broadcasting  # noqa: E402
import seed_data  # noqa: E402

from zoneinfo import ZoneInfo  # noqa: E402

TZ_NAME = "Australia/Sydney"
TZ = ZoneInfo(TZ_NAME)
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S+0000"
PREPOPULATE_PROFILE = "planning_prepopulate_data"

# ---- data -------------------------------------------------------------------------------------------

# Users created by the prepopulate profile get fictional names (the logins stay the same).
USER_NAMES = {
    "admin": ("Luca", "Brandt"),
    "admin1": ("Maren", "Holt"),
    "admin2": ("Daniel", "Okafor"),
    "admin3": ("Priya", "Raman"),
    "admin4": ("Tomas", "Vidal"),
    "test_user": ("Eline", "Sund"),
}

# Desks from the prepopulate profile are renamed, the rest created. `None` as new name deletes the desk.
DESK_RENAMES = {"Sports Desk": "Sports", "Politic Desk": "Politics", "XEditor3 Desk": None}
DESKS = [
    {"name": "Sports", "members": ["admin", "admin1", "admin2", "admin3"]},
    {"name": "Politics", "members": ["admin", "admin1", "admin4"]},
    {"name": "Business", "members": ["admin", "admin3"]},
    {"name": "World", "members": ["admin", "admin4"]},
    {"name": "Culture", "members": ["admin", "test_user"]},
]
CONTENT_PROFILE_LABEL = "Story"
STORY_TEMPLATE = "Story"
ARTICLE_TEMPLATES = [
    {
        "template_name": "Weekly advisory",
        "desk": "Sports",
        "data": {"slugline": "Sport advisory", "headline": "Sport diary for the week ahead"},
    },
]

AGENDAS = [
    {"name": "Sports", "is_enabled": True},
    {"name": "Politics", "is_enabled": True},
    {"name": "Elections 2024", "is_enabled": False},
]

LOCATIONS = [
    {
        "guid": "doc-location-opera-house",
        "name": "Sydney Opera House",
        "unique_name": "Sydney Opera House Bennelong Point",
        "address": {
            "line": ["Bennelong Point"], "area": "Sydney", "city": "Sydney", "state": "New South Wales",
            "postal_code": "2000", "country": "Australia", "type": "arts_centre",
        },
        "position": {"latitude": -33.8568, "longitude": 151.2153},
    },
    {
        "guid": "doc-location-town-hall",
        "name": "Town Hall",
        "unique_name": "Town Hall 483 George St",
        "address": {
            "line": ["483 George St"], "city": "Sydney", "state": "New South Wales", "postal_code": "2000",
            "country": "Australia",
        },
        "position": {"latitude": -33.8731, "longitude": 151.2066},
    },
    {
        "guid": "doc-location-parliament-house",
        "name": "Parliament House",
        "unique_name": "Parliament House Canberra",
        "address": {"city": "Canberra", "state": "Australian Capital Territory", "country": "Australia"},
        "position": {"latitude": -35.3082, "longitude": 149.1244},
    },
]

VOCABULARIES = [
    {
        "_id": "languages", "display_name": "Languages", "type": "manageable", "unique_field": "qcode",
        "service": {"all": 1},
        "items": [
            {"qcode": "nl", "name": "Dutch", "is_active": True},
            {"qcode": "fr", "name": "French", "is_active": True},
            {"qcode": "en", "name": "English", "is_active": True},
            {"qcode": "de", "name": "German", "is_active": True},
        ],
    },
    {
        "_id": "countries", "display_name": "Countries", "type": "manageable", "unique_field": "qcode",
        "items": [
            {"qcode": "AUS", "name": "Australia", "is_active": True},
            {"qcode": "NZL", "name": "New Zealand", "is_active": True},
            {"qcode": "GBR", "name": "United Kingdom", "is_active": True},
        ],
    },
    {
        "_id": "regions", "display_name": "State / Region", "type": "manageable",
        "selection_type": "multi selection", "unique_field": "qcode",
        "items": [
            {"qcode": "NSW", "name": "New South Wales", "is_active": True},
            {"qcode": "VIC", "name": "Victoria", "is_active": True},
            {"qcode": "QLD", "name": "Queensland", "is_active": True},
            {"qcode": "ACT", "name": "Australian Capital Territory", "is_active": True},
        ],
    },
]

CALENDARS = {
    "finance": {"qcode": "finance", "name": "Finance"},
    "sport": {"qcode": "sport", "name": "Sport"},
    "entertainment": {"qcode": "entertainment", "name": "Entertainment"},
}
CONFIRMED = {"qcode": "eocstat:eos5", "name": "Planned, occurs certainly", "label": "Confirmed"}
STATUS = {
    "planned": {"qcode": "ncostat:int", "name": "coverage intended", "label": "Planned"},
    "on_merit": {"qcode": "ncostat:notdec", "name": "coverage not decided yet", "label": "On merit"},
    "not_planned": {"qcode": "ncostat:notint", "name": "coverage not intended", "label": "Not planned"},
}

# `when` is (days from today, "HH:MM") in Sydney wall-clock time.
EVENTS = [
    {
        "guid": "doc-event-council", "slugline": "Council budget vote",
        "name": "City council votes on the 2027 budget",
        "definition_short": "Final vote on the city budget after three weeks of debate.",
        "start": (0, "10:00"), "end": (0, "12:00"), "calendar": "finance", "location": "doc-location-town-hall",
    },
    {
        "guid": "doc-event-run", "slugline": "Harbour run", "name": "Sydney Harbour fun run",
        "definition_short": "Ten kilometre community run from the Opera House to the Harbour Bridge and back.",
        "start": (0, "07:00"), "end": (0, "11:00"), "calendar": "sport", "location": "doc-location-opera-house",
    },
    {
        "guid": "doc-event-opera", "slugline": "Opera premiere", "name": "Premiere of a new Australian opera",
        "definition_short": "First night of a new opera commissioned for the harbour stage.",
        "start": (1, "19:30"), "end": (1, "22:30"), "calendar": "entertainment",
        "location": "doc-location-opera-house",
    },
]

# Coverages: `assign` is (desk, username or None, state). State "draft" keeps the coverage out of the
# workflow; "assigned", "in_progress" and "completed" add it to the workflow and move the assignment there
# through the same endpoints the client uses (assignments/content, assignments/complete).
PLANNING = [
    {
        "guid": "doc-plan-council", "slugline": "Council budget vote",
        "description_text": "Story and pictures on the budget vote.", "date": (0, "12:00"),
        "event": "doc-event-council", "agenda": "Politics", "featured": True,
        "coverages": [
            {"id": "doc-cov-council-text", "type": "text", "slugline": "Council budget vote",
             "due": (0, "14:00"), "status": "planned", "assign": ("Politics", "admin", "in_progress")},
            {"id": "doc-cov-council-picture", "type": "picture", "slugline": "Council budget vote",
             "due": (0, "13:00"), "status": "on_merit", "assign": ("Politics", "admin", "assigned")},
        ],
    },
    {
        "guid": "doc-plan-weather", "slugline": "Weekend weather outlook",
        "description_text": "Forecast for the weekend.", "date": (0, "16:00"), "featured": True,
        "coverages": [
            {"id": "doc-cov-weather", "type": "text", "slugline": "Weekend weather outlook",
             "due": (0, "17:00"), "status": "planned", "assign": ("Politics", None, "draft")},
        ],
    },
    {
        "guid": "doc-plan-run", "slugline": "Harbour run",
        "description_text": "Results and colour from the fun run.", "date": (0, "11:00"),
        "event": "doc-event-run", "agenda": "Sports", "featured": True,
        "coverages": [
            {"id": "doc-cov-run-text", "type": "text", "slugline": "Harbour run",
             "due": (1, "09:00"), "status": "planned", "assign": ("Sports", "admin", "assigned")},
        ],
    },
    {
        "guid": "doc-plan-opera", "slugline": "Opera premiere",
        "description_text": "Review, red carpet pictures and highlights of the premiere.", "date": (1, "18:00"),
        "event": "doc-event-opera",
        "coverages": [
            {"id": "doc-cov-opera-text", "type": "text", "slugline": "Opera review",
             "due": (1, "23:30"), "status": "planned"},
            {"id": "doc-cov-opera-picture", "type": "picture", "slugline": "Opera red carpet",
             "due": (1, "19:00"), "status": "on_merit"},
            {"id": "doc-cov-opera-video", "type": "video", "slugline": "Opera highlights",
             "due": (1, "23:00"), "status": "not_planned"},
        ],
    },
    # Yesterday's work, so that every desk has assignments in several states (Master Desk > Assignments)
    # without adding rows to today's planning list.
    {
        "guid": "doc-plan-retail", "slugline": "Retail sales figures",
        "description_text": "Monthly retail figures and reaction from shop owners.", "date": (-1, "11:00"),
        "coverages": [
            {"id": "doc-cov-retail-text", "type": "text", "slugline": "Retail sales figures",
             "due": (-1, "13:00"), "status": "planned", "assign": ("Business", "admin3", "completed")},
            {"id": "doc-cov-retail-picture", "type": "picture", "slugline": "Retail sales shoppers",
             "due": (-1, "12:00"), "status": "planned", "assign": ("Business", None, "assigned")},
        ],
    },
    {
        "guid": "doc-plan-trade", "slugline": "Trade talks resume",
        "description_text": "Trade ministers meet again after the summer break.", "date": (-1, "09:00"),
        "coverages": [
            {"id": "doc-cov-trade-text", "type": "text", "slugline": "Trade talks resume",
             "due": (-1, "15:00"), "status": "planned", "assign": ("World", "admin4", "in_progress")},
            {"id": "doc-cov-trade-video", "type": "video", "slugline": "Trade talks arrivals",
             "due": (-1, "10:00"), "status": "planned", "assign": ("World", "admin4", "assigned")},
        ],
    },
    {
        "guid": "doc-plan-festival", "slugline": "Film festival opening",
        "description_text": "Opening night of the harbour film festival.", "date": (-1, "18:00"),
        "coverages": [
            {"id": "doc-cov-festival-text", "type": "text", "slugline": "Film festival opening",
             "due": (-1, "22:00"), "status": "planned", "assign": ("Culture", "test_user", "assigned")},
            {"id": "doc-cov-festival-picture", "type": "picture", "slugline": "Film festival red carpet",
             "due": (-1, "19:00"), "status": "planned", "assign": ("Culture", "test_user", "completed")},
        ],
    },
    {
        "guid": "doc-plan-cup", "slugline": "Cup final preview",
        "description_text": "Preview of Saturday's cup final.", "date": (-1, "10:00"),
        "coverages": [
            {"id": "doc-cov-cup-text", "type": "text", "slugline": "Cup final preview",
             "due": (-1, "16:00"), "status": "planned", "assign": ("Sports", "admin2", "in_progress")},
            {"id": "doc-cov-cup-picture", "type": "picture", "slugline": "Cup final training",
             "due": (-1, "11:00"), "status": "planned", "assign": ("Sports", "admin2", "completed")},
        ],
    },
    {
        "guid": "doc-plan-estimates", "slugline": "Budget estimates hearing",
        "description_text": "Treasury officials questioned on the budget estimates.", "date": (-1, "09:30"),
        "coverages": [
            {"id": "doc-cov-estimates-text", "type": "text", "slugline": "Budget estimates hearing",
             "due": (-1, "14:00"), "status": "planned", "assign": ("Politics", "admin1", "completed")},
        ],
    },
]

# The planning items on today's featured stories list. `doc-plan-run` is featured too but not on the list,
# so the Featured Stories window has one entry under Available selections.
FEATURED_LIST = ["doc-plan-council", "doc-plan-weather"]

EVENT_TEMPLATES = [
    {"template_name": "Weekly council meeting", "event": "doc-event-council"},
    {"template_name": "City council session", "event": "doc-event-council"},
    {"template_name": "Home football match", "event": "doc-event-run"},
]

SAVED_FILTERS = [
    {"name": "Sport events this week", "item_type": "events",
     "params": {"calendars": [CALENDARS["sport"]], "date_filter": "this_week"}},
]

EXPORT_TEMPLATES = [
    {"name": "weekly_events", "label": "Weekly events list", "type": "event",
     "data": {"body_html": "{% for item in items %}<p><b>{{ item.name }}</b>, {{ item.schedule }}</p>{% endfor %}"}},
    {"name": "coverage_plan", "label": "Coverage plan", "type": "planning",
     "data": {"body_html": "{% for item in items %}<p>{{ item.slugline }}</p>{% endfor %}"}},
]

# Profile overrides that change the editor for every shot, so they are applied only on request
# (--scenario) right before the shots that need them. Undo them with --reset (planning_types has no DELETE).
SCENARIOS = {
    "multilingual": {
        "event": {
            "name": "event",
            "editor": {"language": {"enabled": True}},
            "schema": {
                "language": {"languages": ["en", "de"], "default_language": "en", "multilingual": True,
                             "required": True},
                "name": {"multilingual": True},
                "slugline": {"multilingual": True},
                "definition_short": {"multilingual": True},
            },
        },
    },
    "grouped-preview": {
        "planning": {
            "name": "planning",
            "editor": {
                "description_text": {"enabled": True, "group": "main", "index": 1},
                "slugline": {"enabled": True, "group": "main", "index": 2},
                "priority": {"enabled": True, "group": "main", "index": 3},
                "planning_date": {"enabled": True, "group": "main", "index": 4},
                "internal_note": {"enabled": True, "group": "main", "index": 5},
                "anpa_category": {"enabled": True, "group": "extra", "index": 1},
                "name": {"enabled": True, "group": None, "index": 6},
                "ednote": {"enabled": False},
                "agendas": {"enabled": False},
                "subject": {"enabled": False},
                "urgency": {"enabled": False},
                "marked_for_not_publication": {"enabled": False},
            },
            "groups": {
                "main": {"_id": "main", "name": "Main", "index": 10, "showBookmark": True, "icon": "align-left",
                         "useToggleBox": False, "translations": {"name": {}}},
                "extra": {"_id": "extra", "name": "Extra", "index": 11, "showBookmark": True,
                          "icon": "info-sign", "useToggleBox": True, "translations": {"name": {}}},
            },
        },
    },
}
# Extra data only the grouped preview shot uses: one planning item with every field of that profile filled.
GROUPED_PREVIEW_PLANNING = {
    "guid": "doc-plan-budget-preview", "slugline": "Budget vote coverage", "name": "City council budget",
    "description_text": "The council votes on next year's budget. Coverage starts with the opening session at "
                        "10:00 and continues through the final vote.",
    "internal_note": "Check with the city desk before posting",
    "anpa_category": [{"qcode": "f", "name": "Finance"}], "priority": 2, "date": (0, "09:00"),
}


# ---- helpers ----------------------------------------------------------------------------------------


def sydney(when):
    days, hhmm = when
    hour, minute = (int(x) for x in hhmm.split(":"))
    today = datetime.datetime.now(TZ).date()
    local = datetime.datetime.combine(today + datetime.timedelta(days=days), datetime.time(hour, minute), TZ)
    return local.astimezone(datetime.timezone.utc).strftime(DATE_FORMAT)


def quote(value):
    return urllib.parse.quote(str(value), safe="")


class Seeder:
    def __init__(self, client):
        self.c = client
        self.users = {}
        self.desks = {}
        self.agendas = {}
        self.profile_id = None
        self.story_template_id = None
        self.sessions = {}
        self.password = None

    # -- lookups

    def load_users(self):
        for user in self.c.get("/users", max_results=200)["_items"]:
            self.users[user["username"]] = user

    def user_id(self, username):
        if username not in self.users:
            raise SeedError("user {!r} does not exist (did the prepopulate reset run?)".format(username))
        return self.users[username]["_id"]

    def load_desks(self):
        self.desks = {d["name"]: d for d in self.c.get("/desks", max_results=200)["_items"]}

    def prepopulate(self, resource, items):
        return self.c.post("/planning_prepopulate", {"resource": resource, "items": items})

    # -- steps

    def seed_users(self):
        self.load_users()
        for username, (first, last) in USER_NAMES.items():
            user = self.users.get(username)
            if not user:
                log("missing", "user", username)
                continue
            display = "{} {}".format(first, last)
            if user.get("display_name") == display:
                log("skip", "user", username, display)
                continue
            updated = self.c.patch("/users/" + user["_id"],
                                   {"first_name": first, "last_name": last, "display_name": display},
                                   user["_etag"])
            user.update(first_name=first, last_name=last, display_name=display, _etag=updated["_etag"])
            log("update", "user", username, display)

    def seed_profile_and_template(self):
        profiles = self.c.get("/content_types", max_results=50)["_items"]
        if not profiles:
            raise SeedError("no content profile found")
        profile = profiles[0]
        self.profile_id = profile["_id"]
        if profile.get("label") != CONTENT_PROFILE_LABEL:
            self.c.patch("/content_types/" + profile["_id"], {"label": CONTENT_PROFILE_LABEL}, profile["_etag"])
            log("update", "profile", CONTENT_PROFILE_LABEL)
        templates = self.c.get("/content_templates", max_results=200)["_items"]
        story = next((t for t in templates if t["template_name"] in (STORY_TEMPLATE, "editor3 template")), None)
        if story is None:
            story = self.c.post("/content_templates", {
                "template_name": STORY_TEMPLATE, "template_type": "create", "is_public": True,
                "data": {"profile": self.profile_id, "type": "text"},
            })
            log("create", "template", STORY_TEMPLATE)
        elif story["template_name"] != STORY_TEMPLATE:
            story.update(self.c.patch("/content_templates/" + story["_id"],
                                      {"template_name": STORY_TEMPLATE}, story["_etag"]))
            log("update", "template", STORY_TEMPLATE)
        self.story_template_id = story["_id"]

    def seed_desks(self):
        self.load_desks()
        for old, new in DESK_RENAMES.items():
            desk = self.desks.get(old)
            if not desk:
                continue
            if new is None:
                try:
                    self.c.delete("/desks/" + desk["_id"], desk["_etag"])
                    log("delete", "desk", old)
                except ApiError as err:
                    log("keep", "desk", old, "delete refused: " + err.message)
            else:
                self.c.patch("/desks/" + desk["_id"], {"name": new}, desk["_etag"])
                log("rename", "desk", old, "-> " + new)
        self.load_desks()
        for spec in DESKS:
            members = [{"user": self.user_id(u)} for u in spec["members"]]
            desk = self.desks.get(spec["name"])
            fields = {
                "members": members,
                "default_content_profile": self.profile_id,
                "default_content_template": self.story_template_id,
            }
            if desk is None:
                desk = self.c.post("/desks", dict(fields, name=spec["name"], desk_type="production"))
                log("create", "desk", spec["name"])
            else:
                self.c.patch("/desks/" + desk["_id"], fields, desk["_etag"])
                log("update", "desk", spec["name"], "members and default template")
        self.load_desks()

        story = self.c.get("/content_templates/" + self.story_template_id)
        desk_ids = [self.desks[d["name"]]["_id"] for d in DESKS]
        if sorted(story.get("template_desks") or []) != sorted(desk_ids):
            self.c.patch("/content_templates/" + story["_id"], {"template_desks": desk_ids}, story["_etag"])
            log("update", "template", STORY_TEMPLATE, "available on every desk")

        # The server lowercases template names on create (not on update), so match case-insensitively and
        # put the capitals back with a PATCH.
        templates = {t["template_name"].lower(): t for t in self.c.get("/content_templates", max_results=200)["_items"]}
        for spec in ARTICLE_TEMPLATES:
            template = templates.get(spec["template_name"].lower())
            if template is None:
                template = self.c.post("/content_templates", {
                    "template_name": spec["template_name"], "template_type": "create", "is_public": True,
                    "template_desks": [self.desks[spec["desk"]]["_id"]],
                    "data": dict(spec["data"], profile=self.profile_id, type="text"),
                })
                log("create", "template", spec["template_name"])
            else:
                log("skip", "template", spec["template_name"])
            if template["template_name"] != spec["template_name"]:
                self.c.patch("/content_templates/" + template["_id"], {"template_name": spec["template_name"]},
                             template["_etag"])

    def seed_vocabularies(self):
        for vocab in VOCABULARIES:
            if self.c.get_optional("/vocabularies/" + vocab["_id"]):
                log("skip", "cv", vocab["_id"])
                continue
            self.prepopulate("vocabularies", [vocab])
            log("create", "cv", vocab["_id"])

    def seed_host_client_vocabularies(self):
        """Vocabularies that extensions of the full Superdesk client read at start-up. Without them the
        client on the docs instance does not start at all (broadcasting reads `rundown_item_types` while
        loading) or shows an "issues with instance configuration" modal to administrators that swallows
        every click (availability-manager needs `availability_manager_tags`). The planning e2e stack does
        not load those extensions, so it never needed them."""
        for spec in seed_broadcasting.VOCABULARIES:
            if self.c.get_optional("/vocabularies/" + spec["_id"]):
                log("skip", "cv", spec["_id"])
                continue
            self.c.post("/vocabularies", {
                "_id": spec["_id"],
                "display_name": spec["display_name"],
                "type": "manageable",
                "unique_field": "qcode",
                "selection_type": "do not show",
                "schema": spec["schema"],
                "items": [dict(item, is_active=True) for item in spec["items"]],
            })
            log("create", "cv", spec["_id"])
        spec = seed_data.AVAILABILITY_TAGS
        if self.c.get_optional("/vocabularies/" + spec["_id"]):
            log("skip", "cv", spec["_id"])
        else:
            self.c.post("/vocabularies", {
                "_id": spec["_id"],
                "display_name": spec["display_name"],
                "type": "manageable",
                "selection_type": "multi selection",
                "service": {"all": 1},
                "unique_field": "qcode",
                "schema": {"name": {"required": True}, "qcode": {"required": True}, "parent": {}},
                "items": [dict(item, is_active=True) for item in spec["items"]],
            })
            log("create", "cv", spec["_id"])

    def seed_locations(self):
        for loc in LOCATIONS:
            if self.c.find_one("/locations", {"unique_name": loc["unique_name"]}):
                log("skip", "location", loc["name"])
                continue
            self.prepopulate("locations", [loc])
            log("create", "location", loc["name"])

    def location_ref(self, guid):
        loc = next(item for item in LOCATIONS if item["guid"] == guid)
        return {"qcode": guid, "name": loc["name"], "address": loc["address"]}

    def seed_agendas(self):
        existing = {a["name"]: a for a in self.c.get("/agenda", max_results=200)["_items"]}
        for spec in AGENDAS:
            agenda = existing.get(spec["name"])
            if agenda is None:
                agenda = self.c.post("/agenda", spec)
                log("create", "agenda", spec["name"])
            else:
                log("skip", "agenda", spec["name"])
            self.agendas[spec["name"]] = agenda["_id"]

    def seed_events(self):
        for spec in EVENTS:
            if self.c.get_optional("/events/" + quote(spec["guid"])):
                log("skip", "event", spec["slugline"])
                continue
            event = {
                "guid": spec["guid"], "type": "event", "state": "draft",
                "slugline": spec["slugline"], "name": spec["name"], "definition_short": spec["definition_short"],
                "dates": {"start": sydney(spec["start"]), "end": sydney(spec["end"]), "tz": TZ_NAME},
                "calendars": [CALENDARS[spec["calendar"]]], "occur_status": CONFIRMED,
            }
            if spec.get("location"):
                event["location"] = [self.location_ref(spec["location"])]
            self.prepopulate("events", [event])
            log("create", "event", spec["slugline"])

    @staticmethod
    def coverage_doc(cov, workflow_status="draft", coverage_id=None):
        return {
            "coverage_id": coverage_id or cov["id"],
            "workflow_status": workflow_status,
            "news_coverage_status": STATUS[cov["status"]],
            "planning": {
                "g2_content_type": cov["type"], "slugline": cov["slugline"], "scheduled": sydney(cov["due"]),
            },
        }

    def seed_planning(self):
        for spec in PLANNING:
            path = "/planning/" + quote(spec["guid"])
            if self.c.get_optional(path):
                log("skip", "planning", spec["slugline"])
                continue
            unassigned = [c for c in spec["coverages"] if not c.get("assign")]
            item = {
                "guid": spec["guid"], "type": "planning", "state": "draft", "slugline": spec["slugline"],
                "description_text": spec["description_text"], "planning_date": sydney(spec["date"]),
                "featured": bool(spec.get("featured")),
                "coverages": [self.coverage_doc(c) for c in unassigned],
            }
            if spec.get("event"):
                item["related_events"] = [{"_id": spec["event"], "link_type": "primary"}]
            if spec.get("agenda"):
                item["agendas"] = [self.agendas[spec["agenda"]]]
            self.prepopulate("planning", [item])
            log("create", "planning", spec["slugline"])
            if len(unassigned) < len(spec["coverages"]):
                self.assign_coverages(spec)

    def assign_coverages(self, spec):
        """Add the assigned coverages with a PATCH, the way the editor saves them, so the server creates the
        assignments, then move each assignment to the state the data asks for."""
        path = "/planning/" + quote(spec["guid"])
        planning = self.c.get(path)
        coverages = list(planning.get("coverages") or [])
        for cov in spec["coverages"]:
            if not cov.get("assign"):
                continue
            desk, username, state = cov["assign"]
            # The server only treats a coverage as new (and creates its assignment) when its id carries the
            # client's temporary prefix; it then replaces the id with a generated guid.
            doc = self.coverage_doc(cov, "draft" if state == "draft" else "active", "tempId-" + cov["id"])
            doc["assigned_to"] = {"desk": self.desks[desk]["_id"], "user": self.user_id(username) if username else None}
            if state != "draft":
                doc["assigned_to"]["state"] = "assigned"
            coverages.append(doc)
        self.c.patch(path, {"coverages": coverages}, planning["_etag"])

        planning = self.c.get(path)
        by_key = {(c["planning"].get("g2_content_type"), c["planning"].get("slugline")): c
                  for c in planning.get("coverages") or []}
        for cov in spec["coverages"]:
            if not cov.get("assign"):
                continue
            desk, username, state = cov["assign"]
            saved = by_key.get((cov["type"], cov["slugline"])) or {}
            assignment_id = (saved.get("assigned_to") or {}).get("assignment_id")
            if not assignment_id and saved:
                assignment = self.c.find_one("/assignments", {"coverage_item": saved["coverage_id"]})
                assignment_id = assignment and assignment["_id"]
            if not assignment_id:
                raise SeedError("no assignment created for coverage {} {}".format(spec["slugline"], cov["type"]))
            self.move_assignment(assignment_id, cov, state, username)
            who = "{} {}".format(*USER_NAMES[username]) if username else "desk only"
            log("assign", "coverage", "{} / {}".format(spec["slugline"], cov["type"]),
                "{}, {} -> {}".format(desk, who, state))

    def client_for(self, username):
        """A session for the assignee. Starting work on a text assignment gives it to the user who starts it,
        so it has to be the assignee. Every prepopulate user except test_user has the administrator's password."""
        if not username or username == self.c.username:
            return self.c
        if username not in self.sessions:
            self.sessions[username] = login(self.c.api_url, username, self.password)
        return self.sessions[username]

    def move_assignment(self, assignment_id, cov, state, username):
        if state in ("draft", "assigned"):
            return
        # Completing a picture or video only confirms availability and keeps the assignee, so the admin does it.
        client = self.client_for(username) if cov["type"] == "text" else self.c
        if cov["type"] == "text":
            client.post("/assignments/content", {"assignment_id": assignment_id})
        elif state == "in_progress":
            raise SeedError("coverage {}: only text assignments can be in progress".format(cov["id"]))
        if state == "completed":
            client.post("/assignments/{}/lock".format(assignment_id), {"lock_action": "complete"})
            assignment = client.get("/assignments/" + assignment_id)
            client.patch("/assignments/complete/" + assignment_id, {}, assignment["_etag"])

    def seed_featured(self):
        for spec in PLANNING:
            if spec.get("featured"):
                planning = self.c.get("/planning/" + quote(spec["guid"]))
                if not planning.get("featured"):
                    self.c.patch("/planning/" + quote(spec["guid"]), {"featured": True}, planning["_etag"])
        today = datetime.datetime.now(TZ).date()
        featured_id = today.strftime("%Y%m%d")
        if self.c.get_optional("/planning_featured/" + featured_id):
            log("skip", "featured", featured_id)
            return
        date = datetime.datetime.combine(today, datetime.time(0, 0), TZ).astimezone(datetime.timezone.utc)
        self.c.post("/planning_featured", {
            "date": date.strftime(DATE_FORMAT), "tz": TZ_NAME, "items": FEATURED_LIST, "posted": False,
        })
        log("create", "featured", featured_id, ", ".join(FEATURED_LIST))

    def seed_event_templates(self):
        existing = {t["template_name"] for t in self.c.get("/events_template", max_results=200)["_items"]}
        for spec in EVENT_TEMPLATES:
            if spec["template_name"] in existing:
                log("skip", "template", spec["template_name"])
                continue
            self.c.post("/events_template", {"template_name": spec["template_name"], "based_on_event": spec["event"]})
            log("create", "template", spec["template_name"], "event template")

    def seed_saved_filters(self):
        existing = {f["name"] for f in self.c.get("/events_planning_filters", max_results=200)["_items"]}
        for spec in SAVED_FILTERS:
            if spec["name"] in existing:
                log("skip", "filter", spec["name"])
                continue
            self.c.post("/events_planning_filters", spec)
            log("create", "filter", spec["name"])

    def seed_export_templates(self):
        existing = {t["name"] for t in self.c.get("/planning_export_templates", max_results=200)["_items"]}
        for spec in EXPORT_TEMPLATES:
            if spec["name"] in existing:
                log("skip", "layout", spec["name"])
                continue
            self.c.post("/planning_export_templates", spec)
            log("create", "layout", spec["name"])

    def unlock_all(self):
        """Release item locks left behind by capture runs (an editor that was not closed keeps its item locked
        for the user's session), through the e2e server's force-unlock endpoint."""
        for resource in ("events", "planning", "assignments"):
            for item in self.c.get("/" + resource, max_results=200)["_items"]:
                if not item.get("lock_user"):
                    continue
                self.c.request("DELETE", "/e2e/force_unlock/{}/{}".format(resource, quote(item["_id"])))
                log("unlock", resource, item.get("slugline") or item.get("planning", {}).get("slugline") or item["_id"])

        # The Featured Stories window holds a lock of its own while it is open.
        if self.c.get("/planning_featured_lock", max_results=10)["_items"]:
            self.c.post("/planning_featured_unlock", {})
            log("unlock", "featured", "Featured Stories")

        # Autosaves of unsaved editor sessions (new items typed in by the capture steps) come back the next time
        # the editor opens, so they go too.
        for resource in ("event_autosave", "planning_autosave"):
            for item in self.c.get("/" + resource, max_results=200)["_items"]:
                self.c.delete("/{}/{}".format(resource, quote(item["_id"])), item["_etag"])
                log("delete", "autosave", item.get("slugline") or item["_id"])

    # -- profile scenarios

    def stored_planning_types(self):
        """Profile overrides stored in the database (the API merges them over the built-in defaults)."""
        return {p["name"]: p for p in self.c.get("/planning_types", max_results=200)["_items"] if p.get("_id")}

    def apply_scenario(self, name):
        """Store the scenario's partial profiles. The API has no DELETE for planning_types, so an override
        is only replaced (PATCH), never removed: `--reset` is what brings the default profiles back."""
        stored = self.stored_planning_types()
        for profile in SCENARIOS[name].values():
            current = stored.get(profile["name"])
            if current:
                self.c.patch("/planning_types/" + current["_id"],
                             {k: v for k, v in profile.items() if k != "name"}, current["_etag"])
                log("update", "profile", profile["name"], "scenario " + name)
            else:
                self.prepopulate("planning_types", [profile])
                log("create", "profile", profile["name"], "scenario " + name)
        if name == "grouped-preview":
            spec = GROUPED_PREVIEW_PLANNING
            if not self.c.get_optional("/planning/" + quote(spec["guid"])):
                item = {k: v for k, v in spec.items() if k != "date"}
                item.update(type="planning", state="draft", planning_date=sydney(spec["date"]))
                self.prepopulate("planning", [item])
                log("create", "planning", spec["slugline"])

    def run(self, scenario):
        self.seed_users()
        self.seed_profile_and_template()
        self.seed_desks()
        self.seed_vocabularies()
        self.seed_host_client_vocabularies()
        self.seed_locations()
        self.seed_agendas()
        self.seed_events()
        self.seed_planning()
        self.seed_featured()
        self.seed_event_templates()
        self.seed_saved_filters()
        self.seed_export_templates()
        self.unlock_all()
        if scenario:
            self.apply_scenario(scenario)


def reset(api_url):
    """Wipe the database with the prepopulate profile. The endpoint is public, and has to be called without a
    session: on an empty database there is no user to log in with yet."""
    Client(api_url).post("/prepopulate", {"profile": PREPOPULATE_PROFILE, "remove_first": True})
    log("reset", "database", PREPOPULATE_PROFILE)


def print_plan(args):
    print("API: {}  user: {}  reset: {}  scenario: {}".format(args.api_url, args.user, args.reset, args.scenario))
    print("today in {}: {}".format(TZ_NAME, datetime.datetime.now(TZ).date()))
    print("users:", ", ".join("{}={} {}".format(u, *n) for u, n in USER_NAMES.items()))
    print("desks:", ", ".join(d["name"] for d in DESKS))
    for spec in EVENTS:
        print("event    {:<28} {} -> {}".format(spec["slugline"], sydney(spec["start"]), sydney(spec["end"])))
    for spec in PLANNING:
        print("planning {:<28} {}".format(spec["slugline"], sydney(spec["date"])))
        for cov in spec["coverages"]:
            print("           {:<8} due {}  {}".format(cov["type"], sydney(cov["due"]), cov.get("assign") or "-"))
    print("agendas:", ", ".join(a["name"] for a in AGENDAS))
    print("event templates:", ", ".join(t["template_name"] for t in EVENT_TEMPLATES))


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Seed the superdesk-planning e2e stack for the Planning screenshots.")
    parser.add_argument("--api-url", default="http://localhost:5021/api", help="API base URL of the planning stack")
    parser.add_argument("--user", default="admin", help="administrator username (default: admin)")
    parser.add_argument("--password", default="admin", help="administrator password (default: admin)")
    parser.add_argument("--dry-run", action="store_true", help="print the plan without connecting to the server")
    parser.add_argument("--reset", action="store_true",
                        help="wipe the database with the planning_prepopulate_data profile first")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS),
                        help="profile overrides for a few shots (undo with --reset)")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.dry_run:
        print_plan(args)
        return 0
    try:
        if args.reset:
            reset(args.api_url)
        client = login(args.api_url, args.user, args.password)
        seeder = Seeder(client)
        seeder.password = args.password
        seeder.run(args.scenario)
    except SeedError as err:
        print("error: {}".format(err), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
