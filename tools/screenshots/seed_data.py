"""Fictional newsroom used by seed.py to populate a Superdesk e2e instance for documentation screenshots.

Everything here is plain data. Edit names, stories or desk layout freely; seed.py validates the data
before sending anything (field lengths, references between desks, users and items, banned words).

All people, places, companies and events are invented. Do not add real people.

Article `key`s are stable identifiers: seed.py turns them into the item guid, which is how it finds
items again on the next run. Changing a key makes seed.py treat the story as a new one.
"""

NEWSROOM = {
    # Prefix of the guid given to every seeded item, so they can be looked up again by id.
    "guid_prefix": "urn:newsml:meridian-news:docs-seed:",
    # Dateline source (agency abbreviation) of the fictional newsroom.
    "source": "MNS",
    # Named zone used for publish schedules and embargoes. Matches DEFAULT_TIMEZONE of the e2e server.
    "timezone": "Europe/London",
    "email_domain": "example.com",
}

# Users that already exist in the e2e `main` snapshot. seed.py never creates, changes or removes them,
# it only looks them up when they are referenced below. Their password is their username
# (see superdesk-client-core/e2e/WRITING_TESTS.md); `admin` uses the --user/--password arguments.
SNAPSHOT_USERS = ["admin", "frodobaggins", "samgamgee"]

# Roles marked `snapshot` exist in the e2e `main` snapshot: they are only created when missing and are
# never removed by --reset.
ROLES = [
    {
        "name": "Editor",
        "description": "Desk editors: edit, publish, schedule and embargo stories, manage the desk workflow",
        "privileges": [
            "archive", "archived", "content_templates", "contacts", "correct", "dashboard", "duplicate",
            "embargo", "fetch", "highlights_read", "hold", "kill", "mark_for_desks", "mark_for_highlights",
            "mark_for_user", "masterdesk", "metadata_uniquename", "monitoring_view", "move", "personal_template",
            "publish", "resend", "rewrite", "saved_searches", "send_to_personal", "spike", "spike_read",
            "takedown", "translate", "unlock", "unspike", "use_global_saved_searches", "view_contacts",
        ],
    },
    {
        "name": "Journalist",
        "description": "Reporters and correspondents: write and file stories, send them to other desks",
        "privileges": [
            "archive", "archived", "content_templates", "dashboard", "duplicate", "fetch", "highlights_read",
            "mark_for_desks", "mark_for_user", "monitoring_view", "move", "personal_template", "rewrite",
            "saved_searches", "send_to_personal", "spike", "spike_read", "translate",
            "use_global_saved_searches", "view_contacts",
        ],
    },
    {
        # Same privileges as the role in the e2e `main` snapshot.
        "name": "Sub Editor",
        "snapshot": True,
        "description": "Desk editing without send-to-personal and without unlocking other users' items",
        "privileges": [
            "archive", "archived", "contacts", "content_templates", "dashboard", "duplicate", "fetch",
            "highlights_read", "mark_for_desks", "mark_for_highlights", "mark_for_user", "metadata_uniquename",
            "monitoring_view", "move", "saved_searches", "spike", "spike_read", "translate", "unspike",
            "use_global_saved_searches", "view_contacts",
        ],
    },
]

# Password of each user is the username, so the screenshot capture script can log in as them.
USERS = [
    {
        "username": "marenholt", "first_name": "Maren", "last_name": "Holt", "sign_off": "MHO",
        "job_title": "Political Editor", "role": "Editor", "default_desk": "Politics",
    },
    {
        "username": "tomasvidal", "first_name": "Tomas", "last_name": "Vidal", "sign_off": "TVI",
        "job_title": "Foreign Affairs Correspondent", "role": "Journalist", "default_desk": "World",
    },
    {
        "username": "priyaraman", "first_name": "Priya", "last_name": "Raman", "sign_off": "PRA",
        "job_title": "Business Editor", "role": "Editor", "default_desk": "Business",
    },
    {
        "username": "danielokafor", "first_name": "Daniel", "last_name": "Okafor", "sign_off": "DOK",
        "job_title": "Sports Reporter", "role": "Journalist", "default_desk": "Sports",
    },
    {
        "username": "elinesund", "first_name": "Eline", "last_name": "Sund", "sign_off": "ESU",
        "job_title": "Arts Correspondent", "role": "Journalist", "default_desk": "Culture",
    },
    {
        "username": "lucabrandt", "first_name": "Luca", "last_name": "Brandt", "sign_off": "LBR",
        "job_title": "Chief Sub Editor", "role": "Sub Editor", "default_desk": "Politics",
    },
]

# The admin user's default desk. Sports is what the e2e `main` snapshot already uses, and most
# screenshots expect the Sports desk to be selected.
ADMIN_DEFAULT_DESK = "Sports"

# Stages flagged `default` ("working" or "incoming") are created automatically by the server with
# every new desk as "Working Stage" and "Incoming Stage"; seed.py renames them to the name given here
# and sets their description. Short names keep the Monitoring group headers readable, which print the
# stage name followed by the word "stage".
# Desks flagged `snapshot` exist in the e2e `main` snapshot: seed.py only adds the listed members and
# never deletes the desk. Their stages are left untouched.
# `monitoring` makes seed.py store explicit monitoring groups on the desk: every stage, the desk output
# and the scheduled desk output, so the "Scheduled Desk Output" group shows regardless of client config.
DESKS = [
    {
        "name": "Sports",
        "snapshot": True,
        "members": ["danielokafor", "lucabrandt"],
        "stages": [{"name": "Working", "default": "working"}, {"name": "Incoming", "default": "incoming"}],
        "monitoring": True,
    },
    {
        "name": "Politics",
        "description": "National politics, elections and parliament",
        "source": "Politics",
        "desk_type": "production",
        "members": ["admin", "marenholt", "tomasvidal", "lucabrandt"],
        "stages": [
            {"name": "Working", "default": "working", "description": "Stories being written and edited"},
            {"name": "Incoming", "default": "incoming", "description": "New copy waiting to be picked up"},
            {"name": "Ready for Review", "description": "Edited copy waiting for the political editor's sign-off"},
            {"name": "Outgoing", "description": "Approved stories ready to publish"},
        ],
        "monitoring": True,
    },
    {
        "name": "Business",
        "description": "Markets, companies and the economy",
        "source": "Business",
        "desk_type": "production",
        "members": ["admin", "priyaraman", "lucabrandt"],
        "stages": [
            {"name": "Working", "default": "working", "description": "Stories being written and edited"},
            {"name": "Incoming", "default": "incoming", "description": "New copy and market wires"},
            {"name": "Ready for Review", "description": "Edited copy waiting for the business editor"},
            {"name": "Outgoing", "description": "Approved stories ready to publish"},
        ],
        "monitoring": True,
    },
    {
        "name": "World",
        "description": "Foreign news, diplomacy and international affairs",
        "source": "World",
        "desk_type": "production",
        "members": ["admin", "tomasvidal", "marenholt"],
        "stages": [
            {"name": "Working", "default": "working", "description": "Stories being written and edited"},
            {"name": "Incoming", "default": "incoming", "description": "Copy from correspondents abroad"},
            {"name": "Outgoing", "description": "Approved stories ready to publish"},
        ],
        "monitoring": True,
    },
    {
        "name": "Culture",
        "description": "Arts, film, books, music and festivals",
        "source": "Culture",
        "desk_type": "production",
        "members": ["admin", "elinesund", "lucabrandt"],
        "stages": [
            {"name": "Working", "default": "working", "description": "Stories being written and edited"},
            {"name": "Incoming", "default": "incoming", "description": "Reviews and listings waiting to be edited"},
            {"name": "Outgoing", "description": "Approved stories ready to publish"},
        ],
        "monitoring": True,
    },
]

# Target of `features.customAuthoringTopbar.sendAndDuplicate` in the superdesk host client config
# (superdesk/client/superdesk.config.js). The e2e client config does not set it. Only created with
# `seed.py --send-and-duplicate-desk`, because its name shows up in every desk list.
SEND_AND_DUPLICATE_DESK = {
    "name": "Test",
    "description": "Target desk of the Send and duplicate shortcut in the authoring top bar",
    "source": "Test",
    "desk_type": "production",
    "members": ["admin"],
    "stages": [
        {"name": "Working", "default": "working"},
        {"name": "Incoming", "default": "incoming"},
        {"name": "Duplicates", "description": "Duplicates created by the Send and duplicate shortcut"},
    ],
    "monitoring": False,
}

# Items of the `categories` vocabulary. The e2e snapshot only has two placeholder entries (qcodes f1 and
# f2): seed.py deactivates those and --reset activates them again.
CATEGORIES = [
    {"qcode": "a", "name": "National"},
    {"qcode": "p", "name": "Politics"},
    {"qcode": "b", "name": "Business"},
    {"qcode": "i", "name": "World"},
    {"qcode": "s", "name": "Sport"},
    {"qcode": "e", "name": "Culture"},
]
HIDDEN_CATEGORY_QCODES = ["f1", "f2"]

# IPTC subject codes (superdesk-core superdesk/io/data/subject_codes.json).
SUBJECTS = {
    "arts": ("01000000", "arts, culture and entertainment"),
    "cinema": ("01005000", "cinema"),
    "culture": ("01022000", "culture (general)"),
    "literature": ("01010000", "literature"),
    "music": ("01011000", "music"),
    "economy": ("04000000", "economy, business and finance"),
    "companies": ("04016000", "company information"),
    "energy": ("04005000", "energy and resource"),
    "macroeconomics": ("04008000", "macro economics"),
    "financial": ("04006000", "financial and business service"),
    "tourism": ("04014000", "tourism and leisure"),
    "construction": ("04004000", "construction and property"),
    "agriculture": ("04001000", "agriculture"),
    "disaster": ("03000000", "disaster and accident"),
    "environment": ("06000000", "environmental issue"),
    "health": ("07000000", "health"),
    "labour": ("09000000", "labour"),
    "politics": ("11000000", "politics"),
    "defence": ("11001000", "defence"),
    "diplomacy": ("11002000", "diplomacy"),
    "election": ("11003000", "election"),
    "government": ("11006000", "government"),
    "parliament": ("11009000", "parliament"),
    "parties": ("11010000", "parties and movements"),
    "social": ("14000000", "social issue"),
    "sport": ("15000000", "sport"),
    "swimming": ("15062000", "swimming"),
    "tennis": ("15065000", "tennis"),
    "sports-event": ("15073000", "sports event"),
    "conflict": ("16000000", "unrest, conflicts and  war"),
}

# qcode -> name, as in the `genre` vocabulary of the e2e snapshot.
GENRES = {
    "Article": "Article (news)",
    "Feature": "Feature",
    "Analysis": "Analysis",
    "Briefs": "Briefs",
    "Review": "Review",
    "Preview": "Preview",
    "Market Report": "Market Report",
    "Results (sport)": "Results (sport)",
    "Interview": "Interview",
}

# Fictional places used in datelines. Aldmark is the newsroom's home country.
PLACES = {
    "arlenport": {"city": "Arlenport", "country": "Aldmark", "tz": "Europe/London"},
    "saltmere": {"city": "Saltmere", "country": "Aldmark", "tz": "Europe/London"},
    "eastbrook": {"city": "Eastbrook", "country": "Aldmark", "tz": "Europe/London"},
    "kestrel-bay": {"city": "Kestrel Bay", "country": "Aldmark", "tz": "Europe/London"},
    "vennhaven": {"city": "Vennhaven", "country": "Aldmark", "tz": "Europe/London"},
    "corvel": {"city": "Corvel", "country": "Valdoria", "tz": "Europe/Berlin"},
    "merrin": {"city": "Merrin", "country": "Tarvos", "tz": "Europe/Berlin"},
    "port-calloway": {"city": "Port Calloway", "country": "Kesmark", "tz": "Europe/Berlin"},
}

# Text articles.
#   stage:   stage name on the desk.
#   action:  what happens after the item is created:
#              None        stays on the stage (saved, unpublished)
#              "publish"   published, shows in the desk output
#              "schedule"  published with a publish schedule in the future (`publish_at`)
#              "spike"     spiked
#   publish_at / embargo: {"days": days from today, "time": "HH:MM"} in NEWSROOM["timezone"].
#   age_minutes: how long ago the item was last modified, so lists show varied, recent times.
ARTICLES = [
    # ---- Politics ---------------------------------------------------------------------------------
    {
        "key": "politics-election-budget",
        "desk": "Politics", "stage": "Working", "author": "marenholt",
        "slugline": "ELECTION-BUDGET",
        "headline": "Coalition unveils election budget with tax cuts for families",
        "abstract": "Finance Minister Ilse Marrow promised lower income tax for households earning under "
                    "60,000 crowns, funded by a new levy on short-term property rentals.",
        "body": [
            "The governing coalition on Monday presented an election-year budget that cuts income tax for "
            "around 1.2 million households, in what opposition parties called a last-minute attempt to "
            "win back voters ahead of the November poll.",
            "Finance Minister Ilse Marrow told the National Assembly the relief would be paid for by a new "
            "levy on short-term property rentals and by freezing the defence budget at this year's level. "
            "\"Families have carried the cost of two hard winters. This budget gives some of that back,\" "
            "she said.",
            "The Civic Union opposition said the figures did not add up. Its finance spokesman, Aron "
            "Pellow, said the rental levy would raise less than half of the 900 million crowns the "
            "government expects.",
        ],
        "genre": "Article", "category": "p", "subjects": ["election", "government"],
        "urgency": 2, "priority": 2, "place": "arlenport", "age_minutes": 18,
    },
    {
        "key": "politics-election-debate",
        "desk": "Politics", "stage": "Incoming", "author": "tomasvidal",
        "slugline": "ELECTION-DEBATE",
        "headline": "Party leaders agree to three TV debates before polling day",
        "abstract": "The first debate, on the economy, will be held in Saltmere on October 28.",
        "body": [
            "The leaders of Aldmark's four largest parties have agreed to take part in three televised "
            "debates before the November election, ending weeks of wrangling over format and venues.",
            "The first debate, on the economy and the cost of living, will be held in Saltmere on October "
            "28. Housing and health will follow in Eastbrook, with a final debate in the capital two days "
            "before polling day.",
        ],
        "genre": "Article", "category": "p", "subjects": ["election", "parties"],
        "urgency": 3, "priority": 4, "place": "arlenport", "age_minutes": 52,
    },
    {
        "key": "politics-parliament-housing",
        "desk": "Politics", "stage": "Ready for Review", "author": "lucabrandt",
        "slugline": "PARLIAMENT-HOUSING",
        "headline": "Assembly committee backs plan to double social housing targets",
        "abstract": "The cross-party housing committee wants 18,000 new social homes a year by 2030.",
        "body": [
            "A cross-party committee of the National Assembly has recommended doubling the annual target "
            "for new social housing, saying the current plan will not keep pace with rising rents in the "
            "capital and along the Kestrel coast.",
            "The committee's report calls for 18,000 new social homes a year by 2030 and for councils to be "
            "allowed to borrow against public land. Committee chair Nadia Esterhal said the proposals had "
            "\"support from every party around the table\".",
            "The housing ministry said it would respond to the report within eight weeks.",
        ],
        "genre": "Article", "category": "p", "subjects": ["parliament", "social"],
        "urgency": 3, "priority": 3, "place": "arlenport", "age_minutes": 95,
    },
    {
        "key": "politics-council-transit",
        "desk": "Politics", "stage": "Working", "author": "tomasvidal",
        "slugline": "COUNCIL-TRANSIT",
        "headline": "Arlenport council approves tram extension to eastern suburbs",
        "abstract": "The 6.4-kilometre line will link the harbour district with Marrow Hill by 2029.",
        "body": [
            "Arlenport city council voted 31 to 14 on Monday evening to approve a 6.4-kilometre extension "
            "of the tram network, linking the harbour district with the fast-growing eastern suburb of "
            "Marrow Hill.",
            "The project is expected to cost 410 million crowns, about a third of which will come from the "
            "national infrastructure fund. Construction is due to begin next spring, with the first trams "
            "running in 2029.",
        ],
        "genre": "Article", "category": "a", "subjects": ["government"],
        "urgency": 4, "priority": 4, "place": "arlenport", "age_minutes": 34,
    },
    {
        "key": "politics-election-poll",
        "desk": "Politics", "stage": "Outgoing", "author": "marenholt",
        "slugline": "ELECTION-POLL",
        "headline": "Poll shows Civic Union narrowing gap to four points",
        "abstract": "The opposition has gained three points in a month as cost of living tops voters' worries.",
        "body": [
            "The opposition Civic Union has narrowed the governing Progressive Alliance's lead to four "
            "points, according to a poll published on Monday, the closest the race has been since the "
            "spring.",
            "The survey of 2,100 adults by the Northgate Institute put the Progressive Alliance on 31 "
            "percent and the Civic Union on 27 percent, with the Green Coast Party unchanged on 14 percent.",
            "Almost half of those asked named the cost of living as their main concern, ahead of housing "
            "and health care.",
        ],
        "genre": "Analysis", "category": "p", "subjects": ["election", "parties"],
        "urgency": 2, "priority": 3, "place": "arlenport", "age_minutes": 140,
        "action": "publish",
    },
    {
        "key": "politics-minister-resigns",
        "desk": "Politics", "stage": "Working", "author": "admin",
        "slugline": "MINISTER-RESIGNS",
        "headline": "Transport minister resigns over ferry contract review",
        "abstract": "Petra Lindqvist steps down after auditors questioned how a 120 million crown ferry "
                    "contract was awarded.",
        "body": [
            "Transport Minister Petra Lindqvist resigned on Monday, two days after the national audit office "
            "said it would review how a 120 million crown ferry contract was awarded last year.",
            "In a short statement, Lindqvist said she had done nothing wrong but did not want the review to "
            "\"become a distraction for the government in the final weeks before the election\".",
            "Prime Minister Corin Ashdale thanked her for her service and said Deputy Minister Jonas Felt "
            "would take over the transport portfolio until the vote.",
        ],
        "genre": "Article", "category": "p", "subjects": ["government", "politics"],
        "urgency": 1, "priority": 1, "place": "arlenport", "age_minutes": 75,
        "action": "publish", "ednote": "Adds prime minister's comments in third paragraph",
    },
    {
        "key": "politics-health-waitlist",
        "desk": "Politics", "stage": "Incoming", "author": "admin",
        "slugline": "HEALTH-WAITLIST",
        "headline": "Hospital waiting lists fall for third straight month",
        "abstract": "The number of patients waiting more than six months for treatment fell by 4 percent.",
        "body": [
            "The number of patients waiting more than six months for planned hospital treatment fell for the "
            "third month in a row in September, health ministry figures showed on Monday.",
        ],
        "genre": "Briefs", "category": "a", "subjects": ["health"],
        "urgency": 4, "priority": 5, "place": "arlenport", "age_minutes": 220,
        "action": "spike",
    },
    {
        "key": "politics-defence-procurement",
        "desk": "Politics", "stage": "Working", "author": "marenholt",
        "slugline": "DEFENCE-PROCUREMENT",
        "headline": "Defence ministry delays patrol vessel order by a year",
        "abstract": "Rising steel prices pushed the cost of four coastal patrol vessels 30 percent over "
                    "budget.",
        "body": [
            "The defence ministry has postponed an order for four coastal patrol vessels by at least a year "
            "after bids came in about 30 percent above budget, officials told the Assembly's defence "
            "committee on Monday.",
            "Deputy Defence Minister Ruth Calloway said rising steel prices and a shortage of shipyard "
            "capacity had pushed up costs. The navy will keep its two oldest vessels in service until "
            "2028 to cover the gap.",
            "Opposition members said the delay left the northern fishing grounds without adequate "
            "protection during the busiest season.",
        ],
        "genre": "Article", "category": "p", "subjects": ["defence", "government"],
        "urgency": 3, "priority": 3, "place": "arlenport", "age_minutes": 12,
    },
    {
        "key": "politics-pension-reform",
        "desk": "Politics", "stage": "Ready for Review", "author": "tomasvidal",
        "slugline": "PENSION-REFORM",
        "headline": "Pension reform bill clears first reading after late-night vote",
        "abstract": "The bill raises the retirement age to 67 by 2034 and passed by 84 votes to 71.",
        "body": [
            "A bill raising the state retirement age to 67 by 2034 cleared its first reading in the National "
            "Assembly shortly before midnight on Monday, by 84 votes to 71.",
            "Labour Minister Henrik Saal said the change was needed to keep the pension fund solvent as the "
            "population ages. Unions have called a national day of protest for next Thursday.",
        ],
        "genre": "Article", "category": "p", "subjects": ["parliament", "labour"],
        "urgency": 2, "priority": 2, "place": "arlenport", "age_minutes": 64,
    },
    # ---- Business ---------------------------------------------------------------------------------
    {
        "key": "business-election-markets",
        "desk": "Business", "stage": "Working", "author": "priyaraman",
        "slugline": "ELECTION-MARKETS",
        "headline": "Bond yields edge higher as investors weigh election risk",
        "abstract": "The ten-year yield rose to 3.9 percent, its highest level since March.",
        "body": [
            "Aldmark's government bond yields rose for a fourth day on Monday as investors priced in the "
            "risk of a closer election and higher public spending after the budget.",
            "The yield on the ten-year bond climbed 6 basis points to 3.9 percent, its highest level since "
            "March. The crown slipped 0.3 percent against the euro.",
            "\"Markets were comfortable with a clear result. A hung assembly is now a real possibility,\" "
            "said Marta Quell, chief economist at Halvard Bank.",
        ],
        "genre": "Market Report", "category": "b", "subjects": ["financial", "election"],
        "urgency": 3, "priority": 3, "place": "arlenport", "age_minutes": 27,
    },
    {
        "key": "business-energy-tariffs",
        "desk": "Business", "stage": "Incoming", "author": "lucabrandt",
        "slugline": "ENERGY-TARIFFS",
        "headline": "Baltrum Energy to raise household tariffs 6 percent in January",
        "abstract": "The country's largest utility blamed higher network charges for the increase.",
        "body": [
            "Baltrum Energy, the country's largest electricity supplier, will raise household tariffs by an "
            "average of 6 percent from January 1, adding about 140 crowns a year to a typical bill.",
            "The company said higher network charges set by the energy regulator accounted for most of the "
            "increase.",
        ],
        "genre": "Article", "category": "b", "subjects": ["energy", "companies"],
        "urgency": 3, "priority": 4, "place": "saltmere", "age_minutes": 48,
    },
    {
        "key": "business-retail-earnings",
        "desk": "Business", "stage": "Ready for Review", "author": "priyaraman",
        "slugline": "RETAIL-EARNINGS",
        "headline": "Kestrel Retail Group profit rises on strong online grocery sales",
        "abstract": "Third-quarter operating profit rose 11 percent to 312 million crowns.",
        "body": [
            "Kestrel Retail Group reported an 11 percent rise in third-quarter operating profit on Monday, "
            "helped by strong growth in online grocery orders and lower transport costs.",
            "Operating profit reached 312 million crowns, ahead of analysts' forecasts of 290 million. Online "
            "sales now make up almost a fifth of the group's grocery revenue.",
            "Chief executive Leona Brandvik said the group would open two more automated distribution "
            "centres next year, in Eastbrook and Vennhaven.",
        ],
        "genre": "Article", "category": "b", "subjects": ["companies"],
        "urgency": 3, "priority": 3, "place": "kestrel-bay", "age_minutes": 9,
    },
    {
        "key": "business-central-bank-rates",
        "desk": "Business", "stage": "Outgoing", "author": "priyaraman",
        "slugline": "CENTRAL-BANK-RATES",
        "headline": "Bank of Aldmark holds key rate at 3.25 percent",
        "abstract": "Policymakers kept rates on hold for a third meeting and signalled no cut before spring.",
        "body": [
            "The Bank of Aldmark kept its main policy rate unchanged at 3.25 percent for a third consecutive "
            "meeting and said it did not expect to cut borrowing costs before the spring.",
            "Governor Elias Mortensen said inflation, at 2.8 percent in September, was falling more slowly "
            "than expected because of rising rents and service prices.",
        ],
        "genre": "Article", "category": "b", "subjects": ["macroeconomics"],
        "urgency": 2, "priority": 2, "place": "arlenport", "age_minutes": 31,
        "action": "publish", "embargo": {"days": 1, "time": "08:00"},
        "ednote": "Embargoed until the rate decision is announced at 08:00",
    },
    {
        "key": "business-airline-merger",
        "desk": "Business", "stage": "Working", "author": "priyaraman",
        "slugline": "AIRLINE-MERGER",
        "headline": "Northwind Air and Coastal Skies agree merger terms",
        "abstract": "The combined airline would carry 9 million passengers a year from four hubs.",
        "body": [
            "Northwind Air and regional carrier Coastal Skies have agreed terms for a merger that would "
            "create a combined airline carrying about 9 million passengers a year, the two companies said.",
            "Coastal Skies shareholders will receive 0.42 Northwind shares for each share they hold. The deal "
            "still needs approval from the competition authority, which is expected to look closely at "
            "routes between Arlenport and the islands.",
        ],
        "genre": "Article", "category": "b", "subjects": ["companies", "tourism"],
        "urgency": 2, "priority": 2, "place": "arlenport", "age_minutes": 58,
        "action": "schedule", "publish_at": {"days": 1, "time": "07:30"},
    },
    {
        "key": "business-port-expansion",
        "desk": "Business", "stage": "Outgoing", "author": "admin",
        "slugline": "PORT-EXPANSION",
        "headline": "Saltmere port expansion wins environmental approval",
        "abstract": "The 600 million crown project will add a deep-water container berth.",
        "body": [
            "A 600 million crown expansion of Saltmere port has won environmental approval, clearing the way "
            "for work on a new deep-water container berth to begin next year.",
            "The environment agency attached 23 conditions, including limits on night-time dredging during "
            "the herring spawning season.",
        ],
        "genre": "Article", "category": "b", "subjects": ["construction", "environment"],
        "urgency": 4, "priority": 4, "place": "saltmere", "age_minutes": 170,
    },
    {
        "key": "business-startup-funding",
        "desk": "Business", "stage": "Working", "author": "priyaraman",
        "slugline": "STARTUP-FUNDING",
        "headline": "Arlenport battery start-up raises 40 million in funding round",
        "abstract": "Voltwharf will use the money to build a pilot plant for sodium-ion cells.",
        "body": [
            "Voltwharf, an Arlenport start-up developing sodium-ion batteries for home energy storage, has "
            "raised 40 million crowns in its second funding round.",
            "The round was led by the state-backed Green Transition Fund. Co-founder Ada Lindholm said the "
            "money would pay for a pilot production line in the harbour district, creating about 60 jobs.",
            "Sodium-ion cells are heavier than lithium-ion batteries but cheaper and easier to source, which "
            "makes them attractive for storage that does not need to move.",
        ],
        "genre": "Feature", "category": "b", "subjects": ["companies", "energy"],
        "urgency": 4, "priority": 5, "place": "arlenport", "age_minutes": 260,
        "action": "publish",
    },
    # ---- World ------------------------------------------------------------------------------------
    {
        "key": "world-election-valdoria",
        "desk": "World", "stage": "Working", "author": "tomasvidal",
        "slugline": "ELECTION-VALDORIA",
        "headline": "Valdoria heads to runoff after no candidate wins majority",
        "abstract": "Former mayor Iva Restrepo and incumbent Mateo Caro will meet in a second round on "
                    "November 2.",
        "body": [
            "Valdoria's presidential election will go to a runoff after none of the seven candidates won an "
            "outright majority in Sunday's first round, the electoral commission said on Monday.",
            "Former Corvel mayor Iva Restrepo led with 38 percent, ahead of incumbent Mateo Caro on 33 "
            "percent. The two will meet in a second round on November 2.",
            "Turnout was 64 percent, the highest since the country's constitution was rewritten in 2011.",
        ],
        "genre": "Article", "category": "i", "subjects": ["election"],
        "urgency": 2, "priority": 2, "place": "corvel", "age_minutes": 22,
    },
    {
        "key": "world-floods-lurenne",
        "desk": "World", "stage": "Incoming", "author": "tomasvidal",
        "slugline": "FLOODS-LURENNE",
        "headline": "Thousands evacuated as Lurenne river bursts its banks",
        "abstract": "About 7,000 people have left their homes in northern Tarvos after three days of rain.",
        "body": [
            "About 7,000 people have been evacuated from towns along the Lurenne river in northern Tarvos "
            "after three days of heavy rain pushed water levels to a 40-year high.",
            "Emergency services said there were no reports of deaths, but two bridges near Merrin had been "
            "closed and rail services to the coast were suspended.",
        ],
        "genre": "Article", "category": "i", "subjects": ["disaster"],
        "urgency": 1, "priority": 1, "place": "merrin", "age_minutes": 6,
    },
    {
        "key": "world-summit-trade",
        "desk": "World", "stage": "Working", "author": "tomasvidal",
        "slugline": "SUMMIT-TRADE",
        "headline": "Northern trade summit opens with tariff truce on the table",
        "abstract": "Ministers from six countries are meeting in Port Calloway to end a dispute over fish "
                    "and timber.",
        "body": [
            "Trade ministers from six northern countries opened a two-day summit in Port Calloway on Monday, "
            "with a proposal to suspend tariffs on fish and timber for 18 months at the top of the agenda.",
            "The dispute began last year when Kesmark imposed duties on processed fish, prompting "
            "retaliatory tariffs on its timber exports.",
            "Aldmark's trade minister, Sabine Rudd, said a truce was \"within reach\" but that any deal "
            "would need to protect coastal fishing communities.",
        ],
        "genre": "Article", "category": "i", "subjects": ["diplomacy", "economy"],
        "urgency": 3, "priority": 3, "place": "port-calloway", "age_minutes": 41,
    },
    {
        "key": "world-ceasefire-talks",
        "desk": "World", "stage": "Outgoing", "author": "marenholt",
        "slugline": "CEASEFIRE-TALKS",
        "headline": "Talks on Dunmarra ceasefire to resume next week, mediators say",
        "abstract": "Negotiators will meet in Port Calloway after a two-week pause.",
        "body": [
            "Talks on a ceasefire in the Dunmarra border region will resume in Port Calloway next week after "
            "a two-week pause, the mediators said in a joint statement on Monday.",
            "Both delegations have agreed to discuss an exchange of detainees and the reopening of the "
            "main border crossing for aid convoys.",
        ],
        "genre": "Article", "category": "i", "subjects": ["conflict", "diplomacy"],
        "urgency": 2, "priority": 2, "place": "port-calloway", "age_minutes": 115,
        "action": "publish",
    },
    {
        "key": "world-drought-harvest",
        "desk": "World", "stage": "Outgoing", "author": "marenholt",
        "slugline": "DROUGHT-HARVEST",
        "headline": "Drought cuts grain harvest across the southern plains",
        "abstract": "Farmers in Tarvos expect wheat yields a quarter below the five-year average.",
        "body": [
            "A summer with almost no rain has cut the wheat harvest across the southern plains of Tarvos by "
            "about a quarter compared with the five-year average, the farmers' union said.",
            "Some growers have started selling livestock early because of a shortage of feed. The union has "
            "asked the government for low-interest loans to help farms through the winter.",
            "Grain buyers in Aldmark said import prices had already risen by about 8 percent since August.",
        ],
        "genre": "Feature", "category": "i", "subjects": ["agriculture", "environment"],
        "urgency": 4, "priority": 4, "place": "merrin", "age_minutes": 300,
    },
    {
        "key": "world-embassy-reopens",
        "desk": "World", "stage": "Incoming", "author": "tomasvidal",
        "slugline": "EMBASSY-REOPENS",
        "headline": "Kesmark reopens embassy in Arlenport after five-year freeze",
        "abstract": "Diplomatic ties were restored in the spring after a dispute over fishing rights.",
        "body": [
            "Kesmark reopened its embassy in Arlenport on Monday, five years after it was closed during a "
            "dispute over fishing rights in the northern straits.",
        ],
        "genre": "Briefs", "category": "i", "subjects": ["diplomacy"],
        "urgency": 4, "priority": 5, "place": "arlenport", "age_minutes": 88,
    },
    # ---- Culture ----------------------------------------------------------------------------------
    {
        "key": "culture-festival-lineup",
        "desk": "Culture", "stage": "Working", "author": "elinesund",
        "slugline": "FESTIVAL-LINEUP",
        "headline": "Harbour Lights Festival announces its biggest programme yet",
        "abstract": "More than 140 concerts, screenings and talks over ten days in November.",
        "body": [
            "The Harbour Lights Festival will stage more than 140 concerts, film screenings and talks over "
            "ten days in November, its largest programme since it began in 2009.",
            "The opening night will feature the National Symphony Orchestra performing a new work by "
            "composer Freya Nordahl, commissioned to mark the reopening of the old customs house as a "
            "concert hall.",
            "Organisers said a third of tickets would be free, and that several venues would be lit by "
            "installations from local artists for the whole festival.",
        ],
        "genre": "Article", "category": "e", "subjects": ["arts", "music"],
        "urgency": 4, "priority": 4, "place": "arlenport", "age_minutes": 44,
    },
    {
        "key": "culture-museum-reopening",
        "desk": "Culture", "stage": "Working", "author": "elinesund",
        "slugline": "MUSEUM-REOPENING",
        "headline": "Maritime museum reopens after three-year restoration",
        "abstract": "The museum's new glass hall houses a restored 19th-century pilot boat.",
        "body": [
            "The Arlenport Maritime Museum reopened to the public on Saturday after a three-year restoration "
            "that cost 85 million crowns.",
            "The centrepiece is a new glass hall built around the Swift, a 19th-century pilot boat that was "
            "raised from the harbour in 2019 and has been conserved ever since.",
            "Director Halvor Engen said the museum hoped to welcome 200,000 visitors in its first year, "
            "almost double its previous attendance.",
        ],
        "genre": "Feature", "category": "e", "subjects": ["culture"],
        "urgency": 5, "priority": 5, "place": "arlenport", "age_minutes": 130,
    },
    {
        "key": "culture-film-awards",
        "desk": "Culture", "stage": "Incoming", "author": "elinesund",
        "slugline": "FILM-AWARDS",
        "headline": "Debut director leads nominations for national film awards",
        "abstract": "Saltwater Hymns received 11 nominations, including best film and best director.",
        "body": [
            "First-time director Mira Kalnes leads the nominations for this year's national film awards, "
            "with her coastal drama Saltwater Hymns shortlisted in 11 categories.",
            "The film, shot in fishing villages along the Kestrel coast with a largely amateur cast, is "
            "nominated for best film, best director and best screenplay. The awards will be presented in "
            "Vennhaven on November 21.",
        ],
        "genre": "Article", "category": "e", "subjects": ["cinema"],
        "urgency": 4, "priority": 4, "place": "vennhaven", "age_minutes": 70,
    },
    {
        "key": "culture-theatre-review",
        "desk": "Culture", "stage": "Outgoing", "author": "elinesund",
        "slugline": "THEATRE-REVIEW",
        "headline": "Review: The Lighthouse Keeper's Daughter finds new light",
        "abstract": "Annika Rehn's revival at the Kestrel Theatre is restrained, funny and beautifully lit.",
        "body": [
            "It is hard to make a play about loneliness feel crowded, but Annika Rehn's revival of The "
            "Lighthouse Keeper's Daughter at the Kestrel Theatre manages to fill the stage with life.",
            "Rehn keeps the action on a single revolving set, the lamp room turning slowly as the seasons "
            "pass. Lotte Brask is superb as the daughter, dry and watchful, and the final scene is lit with "
            "real restraint.",
            "At just under two hours it drags a little in the second act, but this is the best thing the "
            "Kestrel has staged in years.",
        ],
        "genre": "Review", "category": "e", "subjects": ["arts"],
        "urgency": 5, "priority": 6, "place": "kestrel-bay", "age_minutes": 190,
    },
    {
        "key": "culture-book-prize",
        "desk": "Culture", "stage": "Working", "author": "lucabrandt",
        "slugline": "BOOK-PRIZE",
        "headline": "Vennhaven Book Prize goes to first-time novelist",
        "abstract": "Oskar Wendt won for The Tide Tables, a novel about three generations of ferry crews.",
        "body": [
            "Oskar Wendt has won the Vennhaven Book Prize for The Tide Tables, his first novel, about three "
            "generations of a family working the island ferries.",
            "The judges called it \"a quiet book about work and weather that becomes, almost without "
            "warning, a book about love\". The prize is worth 150,000 crowns.",
        ],
        "genre": "Article", "category": "e", "subjects": ["literature"],
        "urgency": 4, "priority": 4, "place": "vennhaven", "age_minutes": 155,
        "action": "publish",
    },
    # ---- Sports -----------------------------------------------------------------------------------
    # Do not use "Football" or "Basketball" in Sports sluglines: the snapshot's only product blocks them,
    # so publishing would not reach the snapshot's subscriber.
    {
        "key": "sports-olympics-swimming",
        "desk": "Sports", "stage": "Working", "author": "danielokafor",
        "slugline": "OLYMPICS-SWIMMING",
        "headline": "Marsh breaks national 200m freestyle record at Olympic trials",
        "abstract": "Lena Marsh, 19, touched in 1:55.84 to secure her place in the Olympic team.",
        "body": [
            "Lena Marsh broke the national 200 metres freestyle record at the Olympic trials in Eastbrook on "
            "Monday, touching in 1 minute 55.84 seconds to secure her place in the team.",
            "The 19-year-old from Saltmere took almost half a second off the record set by her coach, Ingrid "
            "Falk, in 2014. \"I saw the time and I couldn't breathe,\" Marsh said.",
            "The trials continue on Tuesday with the men's 100 metres butterfly.",
        ],
        "genre": "Article", "category": "s", "subjects": ["swimming"],
        "urgency": 2, "priority": 3, "place": "eastbrook", "age_minutes": 15,
    },
    {
        "key": "sports-cycling-tour",
        "desk": "Sports", "stage": "Incoming", "author": "samgamgee",
        "slugline": "CYCLING-TOUR",
        "headline": "Tour of Aldmark route adds two mountain stages",
        "abstract": "Next year's race will finish on the Hallen pass for the first time.",
        "body": [
            "Next year's Tour of Aldmark will include two mountain stages and finish on the Hallen pass for "
            "the first time, organisers said when they presented the route on Monday.",
            "The eight-stage race starts in Kestrel Bay on June 4 and covers 1,240 kilometres.",
        ],
        "genre": "Article", "category": "s", "subjects": ["sport"],
        "urgency": 4, "priority": 5, "place": "kestrel-bay", "age_minutes": 66,
    },
    {
        "key": "sports-marathon-preview",
        "desk": "Sports", "stage": "Working", "author": "danielokafor",
        "slugline": "MARATHON-PREVIEW",
        "headline": "Arlenport Marathon: course record under threat on Sunday",
        "abstract": "Three runners in the field have run faster than the course record this year.",
        "body": [
            "The Arlenport Marathon course record of 2:07:41 could fall on Sunday, with three men in the "
            "field having run faster than that this year.",
            "Organisers have flattened the route along the harbour front and expect cool, still conditions. "
            "About 14,000 runners are entered, a record for the race.",
        ],
        "genre": "Preview", "category": "s", "subjects": ["sports-event"],
        "urgency": 3, "priority": 4, "place": "arlenport", "age_minutes": 38,
        "action": "schedule", "publish_at": {"days": 1, "time": "10:00"},
    },
    {
        "key": "sports-tennis-final",
        "desk": "Sports", "stage": "Working", "author": "danielokafor",
        "slugline": "TENNIS-FINAL",
        "headline": "Aldmark Open final: Brook and Lind meet for the third time",
        "abstract": "Nadia Brook has won both previous meetings with Sofia Lind, both in three sets.",
        "body": [
            "Nadia Brook and Sofia Lind will meet in the Aldmark Open final on Sunday, the third time the "
            "two have played each other this season.",
            "Brook, the top seed, won both earlier matches in three sets. Lind has not dropped a set all "
            "week and beat the defending champion in Saturday's semifinal.",
        ],
        "genre": "Preview", "category": "s", "subjects": ["tennis"],
        "urgency": 3, "priority": 3, "place": "arlenport", "age_minutes": 47,
        "action": "schedule", "publish_at": {"days": 1, "time": "11:00"},
    },
    {
        "key": "sports-rugby-semifinal",
        "desk": "Sports", "stage": "Working", "author": "danielokafor",
        "slugline": "RUGBY-SEMIFINAL",
        "headline": "Eastbrook Rovers name unchanged side for rugby semifinal",
        "abstract": "Coach Viktor Sand keeps faith with the team that beat Saltmere Harriers last week.",
        "body": [
            "Eastbrook Rovers coach Viktor Sand has named an unchanged starting fifteen for Saturday's "
            "national championship semifinal against Kestrel Bay.",
            "Captain Joel Amundsen has recovered from the ankle knock he picked up in last week's win over "
            "Saltmere Harriers and will lead the side from number eight.",
        ],
        "genre": "Article", "category": "s", "subjects": ["sports-event"],
        "urgency": 3, "priority": 4, "place": "eastbrook", "age_minutes": 53,
        "action": "schedule", "publish_at": {"days": 1, "time": "10:00"},
        "embargo": {"days": 1, "time": "12:00"},
        "ednote": "Team news embargoed until the club's announcement at 12:00",
    },
    {
        "key": "sports-sailing-regatta",
        "desk": "Sports", "stage": "Working", "author": "danielokafor",
        "slugline": "SAILING-REGATTA",
        "headline": "Kestrel Cup regatta: home crew takes overall lead",
        "abstract": "Skipper Anja Berg's crew won two of the day's three races.",
        "body": [
            "The Kestrel Bay crew skippered by Anja Berg took the overall lead in the Kestrel Cup regatta on "
            "Monday after winning two of the day's three races.",
            "Results, race 4: 1. Kestrel Bay (Berg), 2. Port Calloway (Hoel), 3. Saltmere (Ruud). Race 5: "
            "1. Kestrel Bay, 2. Saltmere, 3. Vennhaven (Strand). Race 6: 1. Port Calloway, 2. Kestrel Bay, "
            "3. Saltmere.",
        ],
        "genre": "Results (sport)", "category": "s", "subjects": ["sports-event"],
        "urgency": 4, "priority": 5, "place": "kestrel-bay", "age_minutes": 125,
        "action": "publish",
    },
    {
        "key": "sports-rowing-champs",
        "desk": "Sports", "stage": "Working", "author": "danielokafor",
        "slugline": "ROWING-CHAMPS",
        "headline": "Saltmere crews dominate opening day of rowing championships",
        "abstract": "Saltmere Rowing Club won four of the six finals on the Venn river.",
        "body": [
            "Saltmere Rowing Club won four of the six finals on the opening day of the national rowing "
            "championships on the Venn river, including both eights.",
            "Head coach Pia Halvorsen said the club had changed its winter training to spend more time on "
            "the water and less in the gym. \"It has paid off sooner than I expected,\" she said.",
            "The championships finish on Wednesday with the single sculls.",
        ],
        "genre": "Article", "category": "s", "subjects": ["sports-event"],
        "urgency": 4, "priority": 4, "place": "vennhaven", "age_minutes": 24,
    },
    {
        "key": "sports-skiing-season",
        "desk": "Sports", "stage": "Incoming", "author": "admin",
        "slugline": "SKIING-SEASON",
        "headline": "Early snow lets northern ski resorts open a week ahead of plan",
        "abstract": "Three resorts in the Hallen range will open on Saturday.",
        "body": [
            "Three ski resorts in the Hallen range will open on Saturday, a week earlier than planned, after "
            "40 centimetres of snow fell over the weekend.",
        ],
        "genre": "Briefs", "category": "s", "subjects": ["sport", "tourism"],
        "urgency": 5, "priority": 6, "place": "vennhaven", "age_minutes": 102,
    },
    {
        "key": "sports-athletics-trials",
        "desk": "Sports", "stage": "Working", "author": "lucabrandt",
        "slugline": "ATHLETICS-TRIALS",
        "headline": "Sprinters chase world championship places at national trials",
        "abstract": "Only two places are available in the men's 100 metres.",
        "body": [
            "Six men who have run under 10.2 seconds this season will contest two places in the 100 metres "
            "at the national athletics trials in Eastbrook this weekend.",
            "Defending champion Tobias Lerche is the favourite but has raced only twice since a hamstring "
            "injury in June.",
        ],
        "genre": "Preview", "category": "s", "subjects": ["sports-event"],
        "urgency": 3, "priority": 4, "place": "eastbrook", "age_minutes": 81,
    },
]

# Picture items, uploaded as generated images (needs Pillow) or from `seed.py --images-dir`.
# `scene` picks the generated image's look: regatta, marathon, rowing or stadium.
PICTURES = [
    {
        "key": "sports-photo-regatta", "desk": "Sports", "stage": "Incoming", "author": "danielokafor",
        "scene": "regatta", "slugline": "SAILING-REGATTA",
        "headline": "Kestrel Cup regatta, day three",
        "description_text": "Yachts round the outer mark off Kestrel Bay on the third day of the Kestrel Cup "
                            "regatta.",
        "alt_text": "Sailing yachts with white sails on a blue sea",
    },
    {
        "key": "sports-photo-marathon", "desk": "Sports", "stage": "Incoming", "author": "danielokafor",
        "scene": "marathon", "slugline": "MARATHON-PREVIEW",
        "headline": "Arlenport Marathon route along the harbour",
        "description_text": "Early morning on the harbour front in Arlenport, where Sunday's marathon will "
                            "pass twice.",
        "alt_text": "Harbour front at sunrise with warm light over the water",
    },
    {
        "key": "sports-photo-rowing", "desk": "Sports", "stage": "Incoming", "author": "danielokafor",
        "scene": "rowing", "slugline": "ROWING-CHAMPS",
        "headline": "Saltmere crews train on the Venn river",
        "description_text": "Saltmere Rowing Club crews train at dawn on the Venn river before the national "
                            "championships.",
        "alt_text": "Calm river in morning mist with hills behind",
    },
    {
        "key": "sports-photo-stadium", "desk": "Sports", "stage": "Incoming", "author": "danielokafor",
        "scene": "stadium", "slugline": "RUGBY-SEMIFINAL",
        "headline": "Floodlights over Eastbrook Park",
        "description_text": "Floodlights over Eastbrook Park ahead of Saturday's rugby semifinal.",
        "alt_text": "Stadium floodlights against a dark evening sky",
    },
]

# Packages. Items listed here must not be scheduled or spiked: the server refuses both for packaged items.
PACKAGES = [
    {
        "key": "culture-festival-guide",
        "desk": "Culture", "stage": "Working", "author": "elinesund",
        "slugline": "FESTIVAL-GUIDE",
        "headline": "Harbour Lights Festival: the essential guide",
        "abstract": "Concerts, films and installations worth booking ahead.",
        "category": "e", "subjects": ["arts"],
        "items": ["culture-festival-lineup", "culture-film-awards"],
    },
]

# Items marked for a user (the markForUser extension). Marked items must not be locked by another user.
MARKS = [
    {"item": "sports-skiing-season", "user": "admin"},
    {"item": "sports-athletics-trials", "user": "admin"},
    {"item": "politics-pension-reform", "user": "marenholt"},
]

# Items left open for editing (locked) by a user, so Master Desk > Users shows lock counts.
# The user must be a member of the item's desk. Locks last as long as the user's session.
LOCKS = [
    {"item": "politics-defence-procurement", "user": "marenholt"},
    {"item": "politics-council-transit", "user": "tomasvidal"},
    {"item": "world-summit-trade", "user": "tomasvidal"},
    {"item": "business-retail-earnings", "user": "priyaraman"},
    {"item": "sports-rowing-champs", "user": "danielokafor"},
]


# ---- Settings and supporting data --------------------------------------------------------------------
# The blocks below are created after the newsroom (desks, users, items). Each is matched by name (or
# _id) on the next run, so the script stays idempotent. They exist for specific documentation pages;
# the comment on each block names the manifests that need it.

# Story content profile, body field (writing-and-formatting, collaboration-tools). The snapshot ships a
# short list without comments, suggestions or custom blocks. `maxlength` makes the body show its
# character count with the limit and the "Character limit settings" button.
STORY_BODY = {
    "format_options": [
        "h2", "h3", "bold", "italic", "underline", "unordered list", "ordered list", "quote", "link", "embed",
        "media", "table", "multi-line quote", "custom blocks", "remove format", "comments", "annotation",
        "suggestions", "formatting marks", "undo", "redo",
    ],
    "maxlength": 2000,
}

# Custom blocks: vocabularies with field_type 'editor-block' (Settings > Metadata > Custom blocks).
# `template` is the text the block starts with, one line per paragraph.
CUSTOM_BLOCKS = [
    {
        "_id": "fact_box", "display_name": "Fact box",
        "formatting_options": ["bold", "italic", "unordered list", "link"],
        "template": ["Key facts", "Add three to five short points."],
    },
    {
        "_id": "read_more", "display_name": "Read more",
        "formatting_options": ["bold", "link"],
        "template": ["Read more", "Link to related coverage."],
    },
]

# A picture embedded in a story body (edit-media-items/body-media-block): `picture` goes into the body of
# `item` after paragraph `after_paragraph`, with `caption` as the block's caption.
BODY_MEDIA = {
    "item": "sports-olympics-swimming", "picture": "sports-photo-regatta", "after_paragraph": 1,
    "caption": "Yachts round the outer mark on the third day of the Kestrel Cup regatta.",
}

# Extra picture crop size (edit-media-items: the Edit crops button needs at least two sizes).
CROP_SIZES = [{"name": "16-9", "width": 1280, "height": 720}]

# Spell checker dictionary for English. Its words are every word used in this file plus, when the
# file exists, the system word list, so seeded stories show no false spelling warnings.
DICTIONARY = {"name": "English", "language_id": "en", "system_words": "/usr/share/dict/words"}

# Kill and takedown templates from the snapshot get readable text (updates-corrections-kills-and-takedowns).
TEMPLATES = [
    {
        "template_name": "kill", "headline": "KILL NOTICE",
        "body": "This story has been withdrawn for legal reasons. Please remove it from all platforms.",
    },
    {
        "template_name": "takedown", "headline": "TAKEDOWN NOTICE",
        "body": "This story has been taken down. Please remove it from all platforms.",
    },
]

# Two Politics templates admin has used recently, so the Create menu shows 'Recent templates'
# (creating-and-editing-content-items/create-menu). The client keeps that list in the user preference
# `templates:recent`, per desk, newest first. A personal template (is_public False) carries a 'Private' tag.
RECENT_TEMPLATES = {
    "user": "admin",
    "desk": "Politics",
    "templates": [
        {
            "template_name": "Election results brief", "is_public": False,
            "headline": "Results: [constituency]", "body": "Turnout, winner and margin, then reaction from the main parties.",
        },
        {
            "template_name": "Council meeting report", "is_public": True,
            "headline": "Arlenport council: [decision]", "body": "What the council decided, the vote, and what happens next.",
        },
    ],
}

# Desk settings (desk-creation-and-desk-management). `preferred_categories` are qcodes from CATEGORIES;
# they need the categories vocabulary flag 'Available in user/desk preferences', set by seed.py.
DESK_SETTINGS = {
    "Politics": {"email": "politics@meridian.example", "preferred_categories": ["p", "a"]},
}

# Custom workspaces owned by admin, next to 'Workspace 1' from the snapshot (desks-and-custom-workspaces).
WORKSPACES = ["Election night"]

# Items in admin's Personal space: no desk, so they stay personal (desks-and-custom-workspaces).
PERSONAL_ITEMS = [
    {
        "key": "personal-ferry-notes", "slugline": "FERRY-NOTES", "headline": "Notes on the ferry contract review",
        "body": "Questions for the transport committee: who approved the change to the ferry contract, and when.",
    },
    {
        "key": "personal-budget-ideas", "slugline": "BUDGET-IDEAS", "headline": "Ideas for budget explainer",
        "body": "Explain the rental levy with one worked example for a family in Arlenport.",
    },
]

# System messages (system-messages). An active message shows as a toast at the top of every page, so
# `is_active` is only applied with `seed.py --system-message-on`; a plain run leaves all of them inactive.
# Only one may be flagged active.
SYSTEM_MESSAGES = [
    {
        "message_title": "Planned maintenance tonight", "type": "warning", "is_active": True,
        "message": "<p>Superdesk will be unavailable from 22:00 to 22:30 for an upgrade. Save your work before then.</p>",
    },
    {
        "message_title": "New election desk", "type": "primary", "is_active": False,
        "message": "<p>From Monday all election coverage goes through the Politics desk.</p>",
    },
    {
        "message_title": "Wire feed delayed", "type": "alert", "is_active": False,
        "message": "<p>The national wire feed is running about 20 minutes late. We are in touch with the provider.</p>",
    },
]

# Production API keys (superdesk-api). The generated secrets are not printed.
API_KEYS = [
    {"name": "Mobile reporting app", "scope": ["ARCHIVE_READ", "DESKS_READ"]},
    {"name": "Invoicing system", "scope": ["USERS_READ"]},
]

# AI providers (ai-features). Creating a provider does not contact the service.
AI_PROVIDERS = [
    {
        "name": "OpenRouter", "provider_type": "openai_compatible", "base_url": "https://openrouter.ai/api/v1",
        "api_key": "demo-key", "default_model": "openai/gpt-4o-mini",
    },
    {
        "name": "Newsroom local model", "provider_type": "openai_compatible", "base_url": "http://localhost:11434/v1",
        "api_key": "demo-key", "active": False,
    },
]

# Products and subscribers (defining-publishing-in-superdesk, superdesk-api, updates-corrections-kills-
# and-takedowns). 'Subscriber 1' comes from the snapshot and gets the product added to `products` and
# `api_products`. 'Meridian Online' uses an email destination like the snapshot subscriber, so publishing
# to it succeeds against the e2e mail service instead of filling the queue with transmission errors.
PRODUCTS = [{"name": "General news", "product_type": "both"}]
# `token_days`: one Content API token with this expiry, so the subscriber's Content API tab lists a token.
SNAPSHOT_SUBSCRIBER = {
    "name": "Subscriber 1", "products": ["General news"], "api_products": ["General news"], "token_days": 365,
}
SUBSCRIBERS = [
    {
        "name": "Content API client", "email": "content-api@meridian-news.example", "subscriber_type": "digital",
        "products": [], "api_products": ["General news"], "destinations": [],
    },
    {
        "name": "Meridian Online", "email": "online-desk@meridian-news.example", "subscriber_type": "digital",
        "products": ["General news"], "api_products": [],
        "destinations": [{
            "name": "Online desk", "format": "email", "delivery_type": "email",
            "config": {"recipients": "online-desk@meridian-news.example"},
        }],
    },
]

# Saved searches. `owner` is the user who creates it; `subscribe` adds a daily subscription for that user.
# 'Malaysia' is a global saved search in the snapshot that does not fit the fictional newsroom.
SAVED_SEARCHES = [
    {
        "name": "Election coverage", "owner": "admin", "is_global": False,
        "description": "Every item that mentions the election", "q": "election", "repo": "archive,published",
    },
    {
        "name": "Sports results", "owner": "admin", "is_global": True, "subscribe": "admin",
        "description": "Published sport from the last 24 hours", "q": "sport", "repo": "published",
    },
    {
        "name": "Budget watch", "owner": "marenholt", "is_global": True,
        "description": "Budget and tax stories", "q": "budget", "repo": "archive,published",
    },
]
SNAPSHOT_SAVED_SEARCHES_REMOVED = ["Malaysia"]

# Highlights and the items marked for them (highlights). HIGHLIGHT_MARKS maps an article key to the
# highlights it is marked for. The server toggles marks, so seed.py only posts the ones that are missing.
# ELECTION-BUDGET stays unmarked on purpose: a marked item shows a star in its authoring header, and that
# story is opened in authoring by many other pages' shots.
HIGHLIGHTS = [
    {"name": "Top Stories", "desks": ["Politics"], "auto_insert": "now/d"},
    {"name": "Election Watch", "desks": ["Politics"], "auto_insert": "now/w"},
]
HIGHLIGHT_MARKS = {
    "politics-council-transit": ["Top Stories", "Election Watch"],
    "politics-minister-resigns": ["Top Stories"],
}

# Content lists (content-lists extension). `pinned` is the item key fixed at position 0.
CONTENT_LISTS = [
    {
        "name": "Homepage top stories", "limit": 5, "description": "Lead stories for the homepage, in order",
        "enabled": True, "pinned": "politics-minister-resigns",
        "items": [
            "politics-minister-resigns", "business-central-bank-rates", "world-ceasefire-talks",
            "politics-election-poll", "business-startup-funding", "culture-book-prize", "sports-sailing-regatta",
        ],
    },
    {
        "name": "Business briefing", "enabled": True,
        "items": [
            "business-central-bank-rates", "business-startup-funding", "business-airline-merger",
            "business-energy-tariffs",
        ],
    },
    {
        "name": "Election special", "enabled": True,
        "items": [
            "politics-election-poll", "politics-election-budget", "politics-election-debate",
            "business-election-markets", "world-election-valdoria",
        ],
    },
    {
        "name": "Weekend sport", "enabled": True,
        "items": [
            "sports-sailing-regatta", "sports-marathon-preview", "sports-tennis-final", "sports-rugby-semifinal",
        ],
    },
    {"name": "Culture picks", "enabled": False, "items": ["culture-book-prize", "culture-festival-lineup"]},
]
# Created after the lists, so seeding the lists does not trigger them. The .example hosts never answer;
# the server's retries are harmless on the e2e stack.
CONTENT_LIST_WEBHOOKS = [
    {"url": "https://www.meridian-news.example/hooks/content-lists", "enabled": True},
    {"url": "https://staging.meridian-news.example/hooks/content-lists", "enabled": False,
     "excluded_lists": ["Culture picks"]},
]

# Availability management (availability-manager extension). The extension does not start without the
# `availability_manager_tags` vocabulary. Days missing from a user's pattern show as "Not set".
AVAILABILITY_TAGS = {
    "_id": "availability_manager_tags", "display_name": "Regions",
    "items": [
        {"name": "North Aldmark", "qcode": "north"},
        {"name": "Arlenport", "qcode": "north-arlenport", "parent": "north"},
        {"name": "Kestrel Bay", "qcode": "north-kestrel-bay", "parent": "north"},
        {"name": "South Aldmark", "qcode": "south"},
        {"name": "Saltmere", "qcode": "south-saltmere", "parent": "south"},
        {"name": "Eastbrook", "qcode": "south-eastbrook", "parent": "south"},
        {"name": "Vennhaven", "qcode": "south-vennhaven", "parent": "south"},
    ],
}
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
# Per user: tags, then day patterns. A pattern is (days, status, hours or None).
AVAILABILITY = {
    "marenholt": {"tags": ["north-arlenport"], "days": [
        (WEEKDAYS[:5], "available", None), (WEEKDAYS[5:], "unavailable", None)]},
    "tomasvidal": {"tags": ["south-saltmere", "south-eastbrook"], "days": [
        (WEEKDAYS[:4], "available", None), (["friday"], "partial", ("09:00", "13:00")),
        (WEEKDAYS[5:], "unavailable", None)]},
    "priyaraman": {"tags": ["north-arlenport"], "days": [
        (WEEKDAYS[:3], "available", None), (["thursday", "friday"], "partial", ("12:00", "18:00")),
        (WEEKDAYS[5:], "unavailable", None)]},
    "danielokafor": {"tags": ["north-kestrel-bay"], "days": [
        (WEEKDAYS[2:], "available", None), (WEEKDAYS[:2], "unavailable", None)]},
    "elinesund": {"tags": ["south-vennhaven"], "days": [
        (["monday", "wednesday", "friday"], "partial", ("10:00", "16:00"))]},
    "lucabrandt": {"tags": ["south-saltmere"], "days": [(WEEKDAYS, "available", None)]},
    "admin": {"tags": ["north-arlenport"], "days": [(WEEKDAYS[:5], "available", None)]},
}
AVAILABILITY_LANGUAGE = "en"
# Generated entries changed by hand (admin), so the calendar shows 'Modified by'. `days` is relative to today.
AVAILABILITY_OVERRIDES = [{"user": "tomasvidal", "days": 1, "status": "unavailable"}]

# Item comments with @mentions; each gives the mentioned user an unread notification (icons-and-user-
# experience, superdesk-glossary-and-terminology-guide).
COMMENTS = [
    {"item": "politics-pension-reform", "user": "marenholt", "text": "@admin can you check the pension figures before 18:00?"},
    {"item": "politics-council-transit", "user": "tomasvidal", "text": "@admin the council vote moved to Thursday"},
]
