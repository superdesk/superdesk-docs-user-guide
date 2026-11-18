#!/usr/bin/env python3
"""Seed published content, desk moves, editing sessions and a saved report for the Analytics screenshots.

Creates 41 text stories on the Politics, Business, Sports and Culture desks of the newsroom seed.py builds and
publishes 39 of them, then corrects, kills and updates a few, so Content Publishing and Publishing Performance
have several groups and every action colour. For Desk Activity the Politics desk also gets stories sent in from
World, stories sent to World and back, and two spiked drafts. For User Activity one user (USER_ACTIVITY) opens,
edits and closes several Politics stories before they are published. Last, it creates the global Desk Activity
saved report the schedule shot opens, and gives every desk member an email address if one is missing.

Run it after seed.py (the `autodocs` snapshot on the docs instance already contains that seed). The server cannot
backdate anything, so every action is dated when the script runs. Desk Activity and User Activity read archive
statistics, which the server builds from item history once an hour: capture those shots after the next full hour.

Every run is idempotent: stories are found by a fixed guid built from their `key`, updates through the original's
`rewritten_by`, the saved report by name. Standard library only. See SEED.md.

    python3 seed_analytics.py --api-url http://localhost:5011/api [--user admin --password admin] [--dry-run]
"""

import argparse
import datetime
import os
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import seed_data as data  # noqa: E402
from seed import (  # noqa: E402
    BANNED_WORDS,
    MAX_ABSTRACT,
    MAX_HEADLINE,
    MAX_SLUGLINE,
    PUBLISHED_STATES,
    ApiError,
    SeedError,
    article_payload,
    guid_for,
    html_escape,
    item_path,
    log,
    login,
)

# The user whose editing sessions fill the User Activity report. Each story in STORIES with `edit` is opened by
# this user, gets its last paragraph added, and is closed again after `hold` seconds; the report draws one bar
# per session, so the sessions are spread out instead of taking a few milliseconds each.
USER_ACTIVITY = {"user": "marenholt", "pause": 8}

# `relative` is a string because the client's "Last" select stores it that way. The Desk Activity panel itself only
# offers a From/To range in this analytics version, so this relative period can only be set through the API.
SAVED_REPORT = {
    "name": "Politics desk, last 7 days",
    "description": "Incoming and outgoing items on the Politics desk, per day",
    "report": "desk_activity_report",
    "desk": "Politics",
    "params": {
        "dates": {"filter": "relative_days", "relative": "7"},
        "must": {},
        "must_not": {},
        "chart": {"type": "column", "sort_order": "desc", "title": None, "subtitle": None},
        "histogram": {"interval": "daily"},
    },
}

# Desk the `roundtrip` stories are sent to and back from.
ROUNDTRIP_DESK = "World"

# Stories. Fields as in seed_data.ARTICLES (desk, author, slugline, headline, abstract, body, genre, category,
# subjects, place), all created on the desk's Working stage. Extra fields:
#   action:    "publish" (default), "correct", "kill", "update" (published, then rewritten and the rewrite
#              published), "spike" (left unpublished and spiked).
#   via:       desk the story is created on before it is sent to `desk` (a "Sent To" on the Politics desk).
#   roundtrip: sent to ROUNDTRIP_DESK and back before it is published.
#   edit:      seconds USER_ACTIVITY["user"] keeps the story open; the story is created without its last body
#              paragraph and that user adds it.
#   correction / update: the fields the correction or the update changes; `body` replaces the body.
STORIES = [
    # ---- Politics ---------------------------------------------------------------------------------
    {
        "key": "analytics-coalition-talks", "desk": "Politics", "author": "marenholt", "edit": 40,
        "slugline": "COALITION-TALKS",
        "headline": "Coalition partners resume talks on housing bill",
        "abstract": "Negotiators met for four hours in Arlenport and agreed to meet again on Friday.",
        "body": [
            "Negotiators from the three governing parties resumed talks on the stalled housing bill on "
            "Wednesday, a week after the Greens walked out over rent controls.",
            "Housing Minister Odile Fenn said both sides had moved. \"We are closer than we were last week, "
            "and nobody left the room early,\" she said after the meeting.",
        ],
        "genre": "Article", "category": "p", "subjects": ["government", "parties"], "place": "arlenport",
        "action": "correct",
        "correction": {"headline": "Coalition partners resume talks on housing reform bill"},
    },
    {
        "key": "analytics-senate-vote", "desk": "Politics", "author": "tomasvidal", "edit": 25,
        "slugline": "SENATE-VOTE",
        "headline": "Upper house passes ferry subsidy by two votes",
        "abstract": "The subsidy keeps the Saltmere to Kestrel Bay crossing running through the winter.",
        "body": [
            "The upper house approved a 14 million crown subsidy for island ferry routes by 31 votes to 29, "
            "ending a month of uncertainty for coastal towns.",
            "Two opposition senators from the north voted with the government, saying the crossing was a "
            "lifeline for their voters.",
        ],
        "genre": "Article", "category": "p", "subjects": ["parliament"], "place": "arlenport",
    },
    {
        "key": "analytics-mayor-race", "desk": "Politics", "author": "marenholt", "edit": 35,
        "slugline": "MAYOR-RACE",
        "headline": "Eastbrook mayor will not seek a third term",
        "abstract": "Petra Lind said she wants to return to teaching after eight years at city hall.",
        "body": [
            "Eastbrook mayor Petra Lind will not stand in next spring's municipal election, she told the "
            "city council on Wednesday.",
            "Lind, who won her second term with 58 percent of the vote, said she wanted to return to "
            "teaching. Two council members have already said they will run for the post.",
        ],
        "genre": "Article", "category": "a", "subjects": ["election"], "place": "eastbrook",
        "action": "update",
        "update": {
            "headline": "Two council members enter race for Eastbrook mayor",
            "abstract": "Deputy mayor Jonas Vere and councillor Mira Sato announced their bids within hours.",
            "body": [
                "Deputy mayor Jonas Vere and councillor Mira Sato said on Wednesday they would run for mayor of "
                "Eastbrook, hours after Petra Lind announced she would not seek a third term.",
                "Lind has not endorsed either candidate. The election is set for April.",
            ],
        },
    },
    {
        "key": "analytics-defence-review", "desk": "Politics", "author": "lucabrandt", "edit": 30,
        "slugline": "DEFENCE-REVIEW",
        "headline": "Defence review recommends merging two coastal bases",
        "abstract": "The review says the merger would save 40 million crowns a year by 2030.",
        "body": [
            "An independent review of Aldmark's armed forces has recommended merging the naval bases at "
            "Vennhaven and Kestrel Bay, saving around 40 million crowns a year.",
            "The defence ministry said it would respond to the 200-page report before the end of the year.",
        ],
        "genre": "Analysis", "category": "p", "subjects": ["defence"], "place": "vennhaven",
        "action": "correct",
        "correction": {"abstract": "The review says the merger would save 40 million crowns a year by 2031."},
    },
    {
        "key": "analytics-voter-roll", "desk": "Politics", "author": "admin", "edit": 20,
        "slugline": "VOTER-ROLL",
        "headline": "Record number of young voters register before deadline",
        "abstract": "More than 210,000 voters under 25 are on the roll, the electoral office said.",
        "body": [
            "More than 210,000 people under 25 registered to vote before Monday's deadline, the highest number "
            "since the electoral office began publishing figures.",
            "Campaign groups credited a school registration drive that ran in all five regions this autumn.",
        ],
        "genre": "Article", "category": "a", "subjects": ["election"], "place": "arlenport",
    },
    {
        "key": "analytics-budget-hearing", "desk": "Politics", "author": "marenholt", "edit": 30,
        "slugline": "BUDGET-HEARING",
        "headline": "Finance committee questions rental levy forecast",
        "abstract": "Committee members asked the treasury to publish the model behind its revenue estimate.",
        "body": [
            "Members of the parliamentary finance committee on Wednesday pressed treasury officials on how "
            "they reached their forecast for the new short-term rental levy.",
            "The treasury agreed to publish a summary of its model before the budget vote next month.",
        ],
        "genre": "Article", "category": "p", "subjects": ["government", "parliament"], "place": "arlenport",
    },
    {
        "key": "analytics-border-talks", "desk": "Politics", "author": "tomasvidal", "via": "World",
        "slugline": "BORDER-TALKS",
        "headline": "Aldmark and Valdoria agree to reopen border crossing",
        "abstract": "The Corvel crossing will reopen to freight traffic from the first of next month.",
        "body": [
            "Aldmark and Valdoria have agreed to reopen the Corvel border crossing to freight traffic, ending a "
            "six-month closure that cost hauliers millions of crowns.",
            "Foreign Minister Hana Roos said passenger traffic would follow once new customs checks are in "
            "place.",
        ],
        "genre": "Article", "category": "i", "subjects": ["diplomacy"], "place": "corvel",
    },
    {
        "key": "analytics-trade-envoy", "desk": "Politics", "author": "tomasvidal", "via": "World",
        "slugline": "TRADE-ENVOY",
        "headline": "Government names former minister as trade envoy to Tarvos",
        "abstract": "Erik Dahl will lead talks on a fisheries and shipping agreement.",
        "body": [
            "The government has appointed former transport minister Erik Dahl as its special trade envoy to "
            "Tarvos.",
            "Dahl will lead talks on a fisheries and shipping agreement that both sides hope to sign next "
            "year.",
        ],
        "genre": "Article", "category": "i", "subjects": ["diplomacy"], "place": "merrin",
    },
    {
        "key": "analytics-pension-vote", "desk": "Politics", "author": "lucabrandt", "roundtrip": True,
        "slugline": "PENSION-VOTE",
        "headline": "Pension reform clears first reading",
        "abstract": "The bill passed by 88 votes to 71 and now goes to the social affairs committee.",
        "body": [
            "The government's pension reform passed its first reading in the National Assembly by 88 votes to "
            "71 on Wednesday.",
            "The bill now goes to the social affairs committee, where opposition members plan to propose "
            "changes to the retirement age.",
        ],
        "genre": "Article", "category": "p", "subjects": ["parliament", "social"], "place": "arlenport",
    },
    {
        "key": "analytics-embassy-move", "desk": "Politics", "author": "marenholt", "roundtrip": True, "edit": 25,
        "slugline": "EMBASSY-MOVE",
        "headline": "Foreign ministry confirms embassy move in Port Calloway",
        "abstract": "The embassy will move to a new building near the harbour next spring.",
        "body": [
            "Aldmark's embassy in Port Calloway will move to a new building near the harbour next spring, the "
            "foreign ministry said.",
            "The ministry said the current building, in use since 1974, no longer meets security standards.",
        ],
        "genre": "Briefs", "category": "i", "subjects": ["diplomacy"], "place": "port-calloway",
    },
    {
        "key": "analytics-council-pay", "desk": "Politics", "author": "admin",
        "slugline": "COUNCIL-PAY",
        "headline": "Saltmere council freezes members' allowances",
        "abstract": "The freeze applies for two years and saves the city 1.4 million crowns.",
        "body": [
            "Saltmere city council voted on Wednesday to freeze its members' allowances for two years.",
            "The council leader said members could not ask residents to accept higher fees while their own "
            "pay rose.",
        ],
        "genre": "Briefs", "category": "a", "subjects": ["government"], "place": "saltmere",
    },
    {
        "key": "analytics-poll-tracker", "desk": "Politics", "author": "tomasvidal",
        "slugline": "POLL-TRACKER",
        "headline": "Civic Union leads in third poll in a row",
        "abstract": "The opposition party is at 31 percent, two points ahead of the Social Democrats.",
        "body": [
            "The opposition Civic Union leads the governing Social Democrats for the third poll in a row, a "
            "survey for the Meridian News Service shows.",
            "The Greens are steady at 12 percent. One in five voters is still undecided.",
        ],
        "genre": "Analysis", "category": "p", "subjects": ["election", "parties"], "place": "arlenport",
    },
    {
        "key": "analytics-speaker-notes", "desk": "Politics", "author": "lucabrandt", "action": "spike",
        "slugline": "SPEAKER-NOTES",
        "headline": "Speaker sets out timetable for winter session",
        "abstract": "The winter session opens on January 12 with the budget debate.",
        "body": [
            "The Speaker of the National Assembly has set out the timetable for the winter session, which "
            "opens on January 12 with the budget debate.",
        ],
        "genre": "Briefs", "category": "p", "subjects": ["parliament"], "place": "arlenport",
    },
    {
        "key": "analytics-party-congress", "desk": "Politics", "author": "marenholt", "action": "spike",
        "slugline": "PARTY-CONGRESS",
        "headline": "Greens move party congress to Eastbrook",
        "abstract": "The congress was due to be held in Saltmere but the venue is being renovated.",
        "body": [
            "The Greens will hold their party congress in Eastbrook instead of Saltmere, where the planned "
            "venue is being renovated.",
        ],
        "genre": "Briefs", "category": "p", "subjects": ["parties"], "place": "eastbrook",
    },
    # ---- Business ---------------------------------------------------------------------------------
    {
        "key": "analytics-port-profits", "desk": "Business", "author": "priyaraman",
        "slugline": "PORT-PROFITS",
        "headline": "Saltmere port operator posts record quarterly profit",
        "abstract": "Container volumes rose 14 percent as shipping lines moved routes from Merrin.",
        "body": [
            "Saltmere Harbour Group reported a record third-quarter profit of 62 million crowns, helped by a "
            "14 percent rise in container volumes.",
            "Chief executive Lene Brask said two shipping lines had moved their northern routes from Merrin to "
            "Saltmere this year.",
        ],
        "genre": "Article", "category": "b", "subjects": ["companies"], "place": "saltmere",
        "action": "correct",
        "correction": {"abstract": "Container volumes rose 16 percent as shipping lines moved routes from Merrin."},
    },
    {
        "key": "analytics-bank-merger", "desk": "Business", "author": "priyaraman",
        "slugline": "BANK-MERGER",
        "headline": "Two regional banks agree to merge",
        "abstract": "Nordvik Savings and Eastbrook Cooperative Bank will form the country's fourth-largest lender.",
        "body": [
            "Nordvik Savings and Eastbrook Cooperative Bank have agreed to merge, creating Aldmark's "
            "fourth-largest lender with 1.1 million customers.",
            "The banks said no branches would close in the first two years.",
        ],
        "genre": "Article", "category": "b", "subjects": ["financial"], "place": "eastbrook",
        "action": "update",
        "update": {
            "headline": "Regulator to review regional bank merger",
            "abstract": "The competition authority will decide within 90 days whether to open a full inquiry.",
            "body": [
                "The competition authority said on Wednesday it would review the planned merger of Nordvik "
                "Savings and Eastbrook Cooperative Bank.",
                "It will decide within 90 days whether to open a full inquiry.",
            ],
        },
    },
    {
        "key": "analytics-wind-farm", "desk": "Business", "author": "lucabrandt",
        "slugline": "WIND-FARM",
        "headline": "Offshore wind farm wins final planning approval",
        "abstract": "The 600-megawatt project off Kestrel Bay is due to start producing power in 2029.",
        "body": [
            "A 600-megawatt offshore wind farm off Kestrel Bay has won final planning approval after a "
            "three-year review.",
            "The developer said construction would start next summer and create around 900 jobs.",
        ],
        "genre": "Article", "category": "b", "subjects": ["energy"], "place": "kestrel-bay",
    },
    {
        "key": "analytics-retail-sales", "desk": "Business", "author": "priyaraman",
        "slugline": "RETAIL-SALES",
        "headline": "Retail sales fall for second month",
        "abstract": "Spending on clothing and furniture dropped while food sales held steady.",
        "body": [
            "Retail sales fell 0.6 percent in October, the second monthly fall in a row, the statistics office "
            "said.",
            "Spending on clothing and furniture dropped, while food sales were unchanged.",
        ],
        "genre": "Market Report", "category": "b", "subjects": ["macroeconomics"], "place": "arlenport",
    },
    {
        "key": "analytics-airline-fares", "desk": "Business", "author": "lucabrandt",
        "slugline": "AIRLINE-FARES",
        "headline": "Aldair raises winter fares on island routes",
        "abstract": "Fares to Kestrel Bay and Vennhaven rise by up to 12 percent from December.",
        "body": [
            "Aldair will raise fares on its island routes by up to 12 percent from December, citing higher fuel "
            "and airport costs.",
        ],
        "genre": "Briefs", "category": "b", "subjects": ["tourism"], "place": "vennhaven",
        "action": "kill",
    },
    {
        "key": "analytics-housing-starts", "desk": "Business", "author": "priyaraman",
        "slugline": "HOUSING-STARTS",
        "headline": "Housing starts climb to five-year high",
        "abstract": "Builders started 4,300 homes in the third quarter, most of them around the capital.",
        "body": [
            "Builders started work on 4,300 homes in the third quarter, the most in five years, according to "
            "the construction federation.",
            "Most of the new homes are around Arlenport, where land prices have stabilised.",
        ],
        "genre": "Article", "category": "a", "subjects": ["construction"], "place": "arlenport",
    },
    {
        "key": "analytics-farm-prices", "desk": "Business", "author": "lucabrandt",
        "slugline": "FARM-PRICES",
        "headline": "Grain prices ease after strong harvest",
        "abstract": "Wheat prices fell 8 percent from their summer peak.",
        "body": [
            "Grain prices have eased after the strongest harvest in a decade, with wheat down 8 percent from "
            "its summer peak.",
        ],
        "genre": "Market Report", "category": "b", "subjects": ["agriculture"], "place": "eastbrook",
    },
    {
        "key": "analytics-tech-layoffs", "desk": "Business", "author": "priyaraman",
        "slugline": "TECH-JOBS",
        "headline": "Software maker Lumen to cut 300 jobs",
        "abstract": "The company is closing its Saltmere office and moving support work to the capital.",
        "body": [
            "Software maker Lumen will cut 300 jobs and close its Saltmere office by March, the company said.",
            "Unions said they would ask the city to help find work for the staff affected.",
        ],
        "genre": "Article", "category": "b", "subjects": ["companies", "labour"], "place": "saltmere",
    },
    {
        "key": "analytics-inflation", "desk": "Business", "author": "priyaraman",
        "slugline": "INFLATION-DATA",
        "headline": "Inflation slows to 2.4 percent",
        "abstract": "Lower energy prices pulled the annual rate down from 2.9 percent in September.",
        "body": [
            "Annual inflation slowed to 2.4 percent in October from 2.9 percent in September, helped by lower "
            "energy prices.",
            "Economists said the figure made a rate cut at the central bank's December meeting more likely.",
        ],
        "genre": "Article", "category": "b", "subjects": ["macroeconomics"], "place": "arlenport",
    },
    {
        "key": "analytics-shipyard-order", "desk": "Business", "author": "lucabrandt",
        "slugline": "SHIPYARD-ORDER",
        "headline": "Vennhaven shipyard wins ferry order",
        "abstract": "The yard will build two electric ferries for the island routes.",
        "body": [
            "The Vennhaven shipyard has won an order to build two electric ferries for the island routes, "
            "securing work for the next three years.",
        ],
        "genre": "Briefs", "category": "a", "subjects": ["companies"], "place": "vennhaven",
    },
    # ---- Sports -----------------------------------------------------------------------------------
    {
        "key": "analytics-cup-final", "desk": "Sports", "author": "danielokafor",
        "slugline": "CUP-FINAL",
        "headline": "Saltmere Rovers win Kestrel Cup on penalties",
        "abstract": "Goalkeeper Ivo Brandt saved two spot kicks after a 1-1 draw with Eastbrook.",
        "body": [
            "Saltmere Rovers won the Kestrel Cup for the first time in 19 years, beating Eastbrook 4-3 on "
            "penalties after a 1-1 draw.",
            "Goalkeeper Ivo Brandt saved two spot kicks in front of 22,000 fans in Arlenport.",
        ],
        "genre": "Results (sport)", "category": "s", "subjects": ["sports-event"], "place": "arlenport",
        "action": "correct",
        "correction": {"abstract": "Goalkeeper Ivo Brandt saved three spot kicks after a 1-1 draw with Eastbrook."},
    },
    {
        "key": "analytics-coach-signs", "desk": "Sports", "author": "danielokafor",
        "slugline": "COACH-SIGNS",
        "headline": "National team coach signs new four-year contract",
        "abstract": "Anna Koval will lead Aldmark through the next two championships.",
        "body": [
            "National team coach Anna Koval has signed a new four-year contract, the football federation said.",
            "Koval took over in 2023 and led the team to its first championship quarter-final.",
        ],
        "genre": "Article", "category": "s", "subjects": ["sport"], "place": "arlenport",
        "action": "update",
        "update": {
            "headline": "Koval names three new players after contract extension",
            "abstract": "The coach called up two defenders and a goalkeeper for next month's qualifiers.",
            "body": [
                "Anna Koval named three uncapped players in her squad for next month's qualifiers, a day after "
                "signing a new four-year contract.",
            ],
        },
    },
    {
        "key": "analytics-ski-jump", "desk": "Sports", "author": "lucabrandt",
        "slugline": "SKI-JUMP",
        "headline": "Season opener moved after lack of snow",
        "abstract": "The first ski jumping event of the season moves from Eastbrook to the northern hills.",
        "body": [
            "The opening ski jumping event of the season has been moved from Eastbrook because of a lack of "
            "snow, organisers said.",
        ],
        "genre": "Briefs", "category": "s", "subjects": ["sports-event"], "place": "eastbrook",
        "action": "kill",
    },
    {
        "key": "analytics-swim-record", "desk": "Sports", "author": "danielokafor",
        "slugline": "SWIM-RECORD",
        "headline": "Teenager breaks national 200m freestyle record",
        "abstract": "Sixteen-year-old Lea Holm swam 1:56.40 at the winter championships.",
        "body": [
            "Sixteen-year-old Lea Holm broke the national 200 metres freestyle record at the winter "
            "championships in Vennhaven, finishing in 1:56.40.",
        ],
        "genre": "Results (sport)", "category": "s", "subjects": ["swimming"], "place": "vennhaven",
    },
    {
        "key": "analytics-tennis-draw", "desk": "Sports", "author": "danielokafor",
        "slugline": "TENNIS-DRAW",
        "headline": "Top seed faces qualifier in Arlenport Open",
        "abstract": "The draw for next week's indoor tournament was made on Wednesday.",
        "body": [
            "Top seed Marco Vell will face a qualifier in the first round of next week's Arlenport Open.",
        ],
        "genre": "Preview", "category": "s", "subjects": ["tennis"], "place": "arlenport",
    },
    {
        "key": "analytics-league-table", "desk": "Sports", "author": "lucabrandt",
        "slugline": "LEAGUE-ROUNDUP",
        "headline": "Eastbrook go top after late winner",
        "abstract": "A goal in stoppage time gave Eastbrook a 2-1 win at Vennhaven.",
        "body": [
            "Eastbrook moved to the top of the league with a 2-1 win at Vennhaven, scoring the winner in "
            "stoppage time.",
        ],
        "genre": "Results (sport)", "category": "s", "subjects": ["sports-event"], "place": "vennhaven",
    },
    {
        "key": "analytics-stadium-plan", "desk": "Sports", "author": "danielokafor",
        "slugline": "STADIUM-PLAN",
        "headline": "City backs new stadium for Saltmere Rovers",
        "abstract": "The council will lease the club land near the harbour for 50 years.",
        "body": [
            "Saltmere council has agreed to lease land near the harbour to Saltmere Rovers for a new "
            "18,000-seat stadium.",
            "The club hopes to open the stadium in time for the 2029 season.",
        ],
        "genre": "Article", "category": "a", "subjects": ["sport"], "place": "saltmere",
    },
    {
        "key": "analytics-marathon-route", "desk": "Sports", "author": "lucabrandt",
        "slugline": "MARATHON-ROUTE",
        "headline": "Arlenport marathon to finish at the harbour",
        "abstract": "Organisers changed the route to avoid roadworks in the city centre.",
        "body": [
            "Next year's Arlenport marathon will finish at the harbour instead of the city square, organisers "
            "said.",
        ],
        "genre": "Briefs", "category": "s", "subjects": ["sports-event"], "place": "arlenport",
    },
    {
        "key": "analytics-cycling-team", "desk": "Sports", "author": "danielokafor",
        "slugline": "CYCLING-TEAM",
        "headline": "Aldmark names cycling team for track worlds",
        "abstract": "Eight riders will travel to the championships in February.",
        "body": [
            "The cycling federation has named eight riders for the track world championships in February.",
        ],
        "genre": "Briefs", "category": "s", "subjects": ["sport"], "place": "arlenport",
    },
    # ---- Culture ----------------------------------------------------------------------------------
    {
        "key": "analytics-film-festival", "desk": "Culture", "author": "elinesund",
        "slugline": "FILM-FESTIVAL",
        "headline": "Kestrel Bay film festival announces record line-up",
        "abstract": "The festival will screen 140 films from 38 countries in March.",
        "body": [
            "The Kestrel Bay film festival will screen 140 films from 38 countries next March, its largest "
            "programme yet.",
            "Festival director Ines Moor said a third of the films are by first-time directors.",
        ],
        "genre": "Article", "category": "e", "subjects": ["cinema"], "place": "kestrel-bay",
        "action": "correct",
        "correction": {"abstract": "The festival will screen 140 films from 36 countries in March."},
    },
    {
        "key": "analytics-book-prize", "desk": "Culture", "author": "elinesund",
        "slugline": "BOOK-PRIZE",
        "headline": "Debut novel wins National Book Prize",
        "abstract": "Saltmere author Runa Vik won for a novel about three generations of ferry workers.",
        "body": [
            "Runa Vik has won the National Book Prize for her debut novel, about three generations of a family "
            "working on the island ferries.",
            "The jury called it \"a quiet book that stays with you\".",
        ],
        "genre": "Article", "category": "e", "subjects": ["literature"], "place": "saltmere",
        "action": "update",
        "update": {
            "headline": "Book prize winner to donate prize money to library",
            "abstract": "Runa Vik will give the 100,000 crown prize to the Saltmere public library.",
            "body": [
                "Runa Vik, who won the National Book Prize on Wednesday, said she would give the 100,000 crown "
                "prize to the Saltmere public library.",
            ],
        },
    },
    {
        "key": "analytics-orchestra-tour", "desk": "Culture", "author": "lucabrandt",
        "slugline": "ORCHESTRA-TOUR",
        "headline": "National orchestra plans tour of island towns",
        "abstract": "The orchestra will play six concerts in towns without a concert hall.",
        "body": [
            "The National Symphony Orchestra will play six concerts in island towns next summer, in halls, "
            "churches and a boat shed.",
        ],
        "genre": "Article", "category": "e", "subjects": ["music"], "place": "vennhaven",
    },
    {
        "key": "analytics-museum-reopens", "desk": "Culture", "author": "elinesund",
        "slugline": "MUSEUM-REOPENS",
        "headline": "Maritime museum reopens after three-year renovation",
        "abstract": "The museum has a new wing for its collection of fishing boats.",
        "body": [
            "The Maritime Museum in Saltmere reopened on Wednesday after a three-year renovation that added a "
            "wing for its fishing boat collection.",
        ],
        "genre": "Article", "category": "e", "subjects": ["culture"], "place": "saltmere",
    },
    {
        "key": "analytics-theatre-review", "desk": "Culture", "author": "elinesund",
        "slugline": "THEATRE-REVIEW",
        "headline": "A bold staging of an old harbour tale",
        "abstract": "The Eastbrook Playhouse turns a familiar story into a tense two-hander.",
        "body": [
            "The Eastbrook Playhouse has turned a familiar harbour tale into a tense two-hander that runs for "
            "just 80 minutes.",
        ],
        "genre": "Review", "category": "e", "subjects": ["arts"], "place": "eastbrook",
    },
    {
        "key": "analytics-music-awards", "desk": "Culture", "author": "lucabrandt",
        "slugline": "MUSIC-AWARDS",
        "headline": "Folk duo leads music award nominations",
        "abstract": "The Vennhaven duo Salt and Pine has five nominations.",
        "body": [
            "The Vennhaven folk duo Salt and Pine leads the nominations for this year's national music awards "
            "with five.",
        ],
        "genre": "Article", "category": "e", "subjects": ["music"], "place": "vennhaven",
    },
    {
        "key": "analytics-gallery-funding", "desk": "Culture", "author": "elinesund",
        "slugline": "GALLERY-FUNDING",
        "headline": "Regional galleries get extra state funding",
        "abstract": "Twelve galleries outside the capital share 9 million crowns.",
        "body": [
            "Twelve regional galleries will share 9 million crowns of extra state funding next year, the "
            "culture ministry said.",
        ],
        "genre": "Article", "category": "a", "subjects": ["arts"], "place": "arlenport",
    },
    {
        "key": "analytics-film-review", "desk": "Culture", "author": "elinesund",
        "slugline": "FILM-REVIEW",
        "headline": "A lighthouse keeper's last winter, beautifully told",
        "abstract": "Director Ola Brekk's second feature is slow, cold and worth the wait.",
        "body": [
            "Ola Brekk's second feature follows a lighthouse keeper through his last winter on the job. It is "
            "slow, cold and worth the wait.",
        ],
        "genre": "Review", "category": "e", "subjects": ["cinema"], "place": "kestrel-bay",
    },
]

STORY_DEFAULTS = {"stage": "Working", "urgency": 3, "priority": 3, "age_minutes": 2, "created_before_minutes": 5}
ACTIONS = ("publish", "correct", "kill", "update", "spike")


def story_spec(story):
    spec = dict(STORY_DEFAULTS)
    spec.update(story)
    spec.setdefault("action", "publish")
    return spec


def validate():
    problems = []
    keys = set()
    desks = {d["name"]: d for d in data.DESKS}
    users = {u["username"] for u in data.USERS} | set(data.SNAPSHOT_USERS)
    for story in STORIES:
        spec = story_spec(story)
        label = spec["key"]
        if label in keys:
            problems.append("{}: duplicate key".format(label))
        keys.add(label)
        if spec["action"] not in ACTIONS:
            problems.append("{}: unknown action {!r}".format(label, spec["action"]))
        for desk in (spec["desk"], spec.get("via")):
            if desk and desk not in desks:
                problems.append("{}: unknown desk {!r}".format(label, desk))
        if spec["author"] not in users:
            problems.append("{}: unknown author {!r}".format(label, spec["author"]))
        if spec["category"] not in {c["qcode"] for c in data.CATEGORIES}:
            problems.append("{}: unknown category {!r}".format(label, spec["category"]))
        if spec["genre"] not in data.GENRES or spec["place"] not in data.PLACES:
            problems.append("{}: unknown genre or place".format(label))
        if any(s not in data.SUBJECTS for s in spec["subjects"]):
            problems.append("{}: unknown subject".format(label))
        if spec.get("edit") and len(spec["body"]) < 2:
            problems.append("{}: an edited story needs two body paragraphs".format(label))
        if spec["action"] == "correct" and not spec.get("correction"):
            problems.append("{}: action 'correct' needs `correction`".format(label))
        if spec["action"] == "update" and not spec.get("update"):
            problems.append("{}: action 'update' needs `update`".format(label))
        texts = [spec, spec.get("correction") or {}, spec.get("update") or {}]
        for text in texts:
            for field, limit in (("slugline", MAX_SLUGLINE), ("headline", MAX_HEADLINE), ("abstract", MAX_ABSTRACT)):
                if len(text.get(field) or "") > limit:
                    problems.append("{}: {} longer than {}".format(label, field, limit))
            for value in [text.get("headline"), text.get("abstract")] + list(text.get("body") or []):
                if value and BANNED_WORDS.search(value):
                    problems.append("{}: banned word in {!r}".format(label, value[:40]))
    if problems:
        raise SeedError("seed_analytics.py data problems:\n  " + "\n  ".join(problems))


def publish_action_path(action, item_id):
    """Path of the publish actions, which put the action before the id (PATCH /archive/correct/<id>)."""
    return "/archive/{}/{}".format(action, urllib.parse.quote(item_id, safe=":"))


def body_html(paragraphs):
    return "".join("<p>{}</p>".format(html_escape(p)) for p in paragraphs)


class Seeder:
    def __init__(self, args):
        self.args = args
        self.api_url = args.api_url.rstrip("/")
        self.admin = login(self.api_url, args.user, args.password)
        self.sessions = {args.user: self.admin}
        self.user_ids = {}
        self.display_names = {}
        self.desks = {}
        self.stage_ids = {}
        self.profile_id = None

    def client_for(self, username):
        username = self.args.user if username == "admin" else username
        if username not in self.sessions:
            # The seeded users and the snapshot users use their username as password.
            self.sessions[username] = login(self.api_url, username, username)
            log("login", "user", username)
        return self.sessions[username]

    def load_reference_data(self):
        for username in sorted({u["username"] for u in data.USERS} | set(data.SNAPSHOT_USERS)):
            name = self.args.user if username == "admin" else username
            user = self.admin.find_one("/users", {"username": name})
            if user is None:
                raise SeedError("user {} does not exist; run seed.py first".format(name))
            self.user_ids[username] = str(user["_id"])
            self.display_names[username] = user.get("display_name") or username
        for desk_name in {d["name"] for d in data.DESKS}:
            desk = self.admin.find_one("/desks", {"name": desk_name})
            if desk is None:
                raise SeedError("desk {} does not exist; run seed.py first".format(desk_name))
            self.desks[desk_name] = desk
            for stage in self.admin.find_all("/stages", {"desk": str(desk["_id"])}):
                self.stage_ids[(desk_name, stage["name"])] = str(stage["_id"])
        profile = self.admin.find_one("/content_types", {"label": "Story"})
        self.profile_id = str(profile["_id"]) if profile else None

    def ctx(self):
        return {
            "user_ids": self.user_ids,
            "display_names": self.display_names,
            "desk_ids": {name: str(desk["_id"]) for name, desk in self.desks.items()},
            "stage_ids": self.stage_ids,
            "profile_id": self.profile_id,
        }

    def get(self, guid):
        return self.admin.get(item_path(guid))

    def task_for(self, desk_name):
        desk = self.desks[desk_name]
        return {"desk": str(desk["_id"]), "stage": str(desk["incoming_stage"])}

    def unlock(self, item):
        if item.get("lock_user"):
            self.admin.post(item_path(item["_id"], "unlock"), {})
            item = self.get(item["_id"])
        return item

    # -- users

    def ensure_emails(self):
        for spec in data.USERS:
            user = self.admin.find_one("/users", {"username": spec["username"]})
            if user.get("email"):
                log("skip", "email", spec["username"], user["email"])
                continue
            email = "{}.{}@{}".format(spec["first_name"].lower(), spec["last_name"].lower(),
                                      data.NEWSROOM["email_domain"])
            self.admin.patch("/users/" + str(user["_id"]), {"email": email}, user["_etag"])
            log("update", "email", spec["username"], email)

    # -- stories

    def ensure_created(self, spec):
        guid = guid_for(spec["key"])
        item = self.admin.get_optional(item_path(guid))
        if item is not None:
            log("skip", "story", spec["slugline"], "exists ({})".format(item.get("state")))
            return item
        created_on = dict(spec, desk=spec.get("via") or spec["desk"])
        payload = article_payload(created_on, self.ctx())
        if spec.get("edit"):
            payload["body_html"] = body_html(spec["body"][:-1])
        self.client_for(spec["author"]).post("/archive", payload)
        log("create", "story", spec["slugline"], "{} by {}".format(created_on["desk"], spec["author"]))
        return self.get(guid)

    def is_published(self, item):
        return item.get("state") in PUBLISHED_STATES

    def ensure_edited(self, spec, item):
        """One editing session: lock, add the last paragraph, wait, unlock, as USER_ACTIVITY["user"]."""
        if not spec.get("edit") or self.is_published(item) or html_escape(spec["body"][-1]) in item.get("body_html", ""):
            return item
        username = USER_ACTIVITY["user"]
        client = self.client_for(username)
        item = self.unlock(item)
        locked = client.post(item_path(item["_id"], "lock"), {"lock_action": "edit"})
        time.sleep(spec["edit"] / 2)
        client.patch(item_path(item["_id"]), {"body_html": body_html(spec["body"])}, locked["_etag"])
        time.sleep(spec["edit"] / 2)
        client.post(item_path(item["_id"], "unlock"), {})
        log("edit", "story", spec["slugline"], "open {} s by {}".format(spec["edit"], username))
        time.sleep(USER_ACTIVITY["pause"])
        return self.get(item["_id"])

    def move(self, item, desk_name):
        item = self.unlock(item)
        self.admin.post(item_path(item["_id"], "move"), {"task": self.task_for(desk_name)})
        return self.get(item["_id"])

    def ensure_desk(self, spec, item):
        if self.is_published(item) or item.get("state") == "spiked":
            return item
        if spec.get("via") and item["task"]["desk"] != str(self.desks[spec["desk"]]["_id"]):
            item = self.move(item, spec["desk"])
            log("send", "story", spec["slugline"], "{} to {}".format(spec["via"], spec["desk"]))
        if spec.get("roundtrip"):
            item = self.move(item, ROUNDTRIP_DESK)
            item = self.move(item, spec["desk"])
            log("send", "story", spec["slugline"], "{} to {} and back".format(spec["desk"], ROUNDTRIP_DESK))
        return item

    def ensure_published(self, slugline, item):
        if self.is_published(item):
            log("skip", "publish", slugline, item["state"])
            return item
        item = self.unlock(item)
        self.admin.patch(item_path(item["_id"], "publish"), {"state": "published"}, item["_etag"])
        log("publish", "story", slugline)
        return self.get(item["_id"])

    def ensure_corrected(self, spec, item):
        if item.get("state") == "corrected":
            log("skip", "correct", spec["slugline"])
            return
        item = self.unlock(item)
        self.admin.patch(publish_action_path("correct", item["_id"]), spec["correction"], item["_etag"])
        log("correct", "story", spec["slugline"], ", ".join(sorted(spec["correction"])))

    def ensure_killed(self, spec, item):
        if item.get("state") == "killed":
            log("skip", "kill", spec["slugline"])
            return
        item = self.unlock(item)
        self.admin.patch(publish_action_path("kill", item["_id"]), {}, item["_etag"])
        log("kill", "story", spec["slugline"])

    def ensure_updated(self, spec, item):
        update = spec["update"]
        if item.get("rewritten_by"):
            rewrite = self.get(item["rewritten_by"])
        else:
            item = self.unlock(item)
            created = self.admin.post(item_path(item["_id"], "rewrite"), {"desk_id": str(self.desks[spec["desk"]]["_id"])})
            rewrite = self.get(created["_id"])
            log("rewrite", "story", spec["slugline"])
        if self.is_published(rewrite):
            log("skip", "update", spec["slugline"], rewrite["state"])
            return
        rewrite = self.unlock(rewrite)
        changes = {k: update[k] for k in ("headline", "abstract") if k in update}
        changes["body_html"] = body_html(update["body"])
        rewrite.update(self.admin.patch(item_path(rewrite["_id"]), changes, rewrite["_etag"]))
        self.ensure_published(spec["slugline"] + " (update)", self.get(rewrite["_id"]))

    def ensure_spiked(self, spec, item):
        if item.get("state") == "spiked":
            log("skip", "spike", spec["slugline"])
            return
        item = self.unlock(item)
        self.admin.patch(item_path(item["_id"], "spike"), {"state": "spiked"}, item["_etag"])
        log("spike", "story", spec["slugline"])

    def ensure_stories(self):
        specs = [story_spec(s) for s in STORIES]
        items = {spec["key"]: self.ensure_created(spec) for spec in specs}
        for spec in specs:
            items[spec["key"]] = self.ensure_edited(spec, items[spec["key"]])
        for spec in specs:
            items[spec["key"]] = self.ensure_desk(spec, items[spec["key"]])
        for spec in specs:
            if spec["action"] != "spike":
                items[spec["key"]] = self.ensure_published(spec["slugline"], items[spec["key"]])
        for spec in specs:
            item = items[spec["key"]]
            if spec["action"] == "correct":
                self.ensure_corrected(spec, item)
            elif spec["action"] == "kill":
                self.ensure_killed(spec, item)
            elif spec["action"] == "update":
                self.ensure_updated(spec, item)
            elif spec["action"] == "spike":
                self.ensure_spiked(spec, item)

    # -- saved report

    def ensure_saved_report(self):
        spec = SAVED_REPORT
        existing = self.admin.find_one("/saved_reports", {"name": spec["name"]})
        if existing is not None:
            log("skip", "report", spec["name"])
            return
        params = dict(spec["params"], desk=str(self.desks[spec["desk"]]["_id"]))
        self.admin.post("/saved_reports", {
            "name": spec["name"],
            "description": spec["description"],
            "report": spec["report"],
            "params": params,
            "is_global": True,
        })
        log("create", "report", spec["name"], "global")

    def run(self):
        self.load_reference_data()
        self.ensure_emails()
        self.ensure_stories()
        self.ensure_saved_report()
        print("\nDone at {} UTC. Desk Activity and User Activity show this activity after the next hourly statistics "
              "run.".format(datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M")))


def print_plan(args):
    print("API: {}  user: {}".format(args.api_url, args.user))
    specs = [story_spec(s) for s in STORIES]
    for spec in specs:
        extra = []
        if spec.get("via"):
            extra.append("via " + spec["via"])
        if spec.get("roundtrip"):
            extra.append("to {} and back".format(ROUNDTRIP_DESK))
        if spec.get("edit"):
            extra.append("edited {} s by {}".format(spec["edit"], USER_ACTIVITY["user"]))
        print("story  {:<16} {:<9} {:<13} {:<8} {}".format(
            spec["slugline"], spec["desk"], spec["author"], spec["action"], ", ".join(extra)))
    published = [s for s in specs if s["action"] != "spike"]
    print("{} stories, {} published, {} updates published".format(
        len(specs), len(published), sum(1 for s in specs if s["action"] == "update")))
    print("report {} ({}, global)".format(SAVED_REPORT["name"], SAVED_REPORT["report"]))


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Seed published stories, desk activity, editing sessions and a "
                                                 "saved report for the Analytics screenshots.")
    parser.add_argument("--api-url", default="http://localhost:5011/api", help="API base URL")
    parser.add_argument("--user", default="admin", help="administrator username (default: admin)")
    parser.add_argument("--password", default="admin", help="administrator password (default: admin)")
    parser.add_argument("--dry-run", action="store_true", help="print the plan without connecting to the server")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        validate()
        if args.dry_run:
            print_plan(args)
            return 0
        Seeder(args).run()
    except ApiError as err:
        print("\nERROR: the server rejected a request\n{}".format(err), file=sys.stderr)
        return 1
    except SeedError as err:
        print("\nERROR: {}".format(err), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
