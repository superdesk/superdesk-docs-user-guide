# Seeding a newsroom for screenshots

`seed.py` fills a local Superdesk e2e instance with a fictional newsroom (the Meridian News Service, in the invented country of Aldmark) so documentation screenshots look like real newsroom work instead of a test run. All content lives in `seed_data.py` as plain Python data, so you can change names, stories and desk layout without touching the logic.

It only uses the Python standard library. Pillow is used to draw the picture items when it is installed; without it, pictures are skipped unless you pass `--images-dir`.

## Running it

Start the e2e stack from `superdesk-client-core` (`./e2e/scripts/e2e-up.sh`, API on port 5002), then:

```bash
# optional but recommended: start from a clean e2e "main" snapshot
curl -X POST http://localhost:5002/api/restore_record -H 'Content-Type: application/json' -d '{"name": "main"}'

python3 seed.py --api-url http://localhost:5002/api
```

Options:

- `--user` / `--password`: administrator to run as (default `admin` / `admin`).
- `--dry-run`: validate `seed_data.py` and print the plan. Sends no requests, so it works without a server.
- `--reset`: remove what the script created, as far as the API allows (see below).
- `--images-dir DIR`: upload `.jpg`/`.png` files from `DIR` (in sorted order) instead of generated pictures. Use this when the photo grid needs to look like real photography.
- `--system-message-on`: activate the system message flagged `is_active` in `SYSTEM_MESSAGES` (see below). Without the flag every seeded system message is left inactive, and a run without it switches an active one off again.
- `--send-and-duplicate-desk`: also create the `Test` desk with a `Working` stage. The superdesk host client config (`superdesk/client/superdesk.config.js`) points `features.customAuthoringTopbar.sendAndDuplicate` at that desk, and the button only shows when it exists. The e2e client config does not set `customAuthoringTopbar` at all, so this is off by default to keep a desk called "Test" out of every other screenshot.

Every run is idempotent. Roles and desks are matched by name, users by username, and items by a fixed guid built from their `key` in `seed_data.py`, so a second run only logs `skip` lines. Each created or skipped object is logged on its own line. Any 4xx from the server stops the run and prints the server's error body.

`restore_record` wipes the database, so run the seed again after every snapshot restore (the Playwright specs restore the snapshot before each test that changes data).

## What it creates

- **Roles**: `Editor` and `Journalist`. `Sub Editor` already exists in the snapshot and is reused.
- **Users** (password is the username): `marenholt` (Maren Holt, Political Editor, Editor), `tomasvidal` (Tomas Vidal, Foreign Affairs Correspondent, Journalist), `priyaraman` (Priya Raman, Business Editor, Editor), `danielokafor` (Daniel Okafor, Sports Reporter, Journalist), `elinesund` (Eline Sund, Arts Correspondent, Journalist), `lucabrandt` (Luca Brandt, Chief Sub Editor, Sub Editor). Each gets a default desk, sign-off and byline.
- **Desks** (production type, Story profile and story template): `Politics` and `Business` with Working, Incoming, Ready for Review and Outgoing; `World` and `Culture` with Working, Incoming and Outgoing. The server creates the two default stages as "Working Stage" and "Incoming Stage"; the seed renames them to the short names so that Monitoring group headers read "Working stage" instead of "Working Stage stage". Admin is a member of all of them. `Sports` from the snapshot gets `danielokafor` and `lucabrandt` as extra members and its default stages are renamed the same way. The admin user's default desk stays Sports.
- **Monitoring groups** on those five desks: every stage, the desk output and the scheduled desk output, so the "Scheduled Desk Output" group shows even when the client config has no `monitoring.scheduled`.
- **Categories vocabulary**: National, Politics, Business, World, Sport and Culture. The snapshot's two placeholder categories are deactivated.
- **36 text articles** across the five desks, with sluglines, headlines, abstracts, two or three body paragraphs, datelines, IPTC subjects, genres, urgency and priority, authors and recent modification times. Their states:
  - 7 published (Politics, Business, World, Culture and Sports desk outputs), one of them with an embargo (`CENTRAL-BANK-RATES`, embargo tomorrow 08:00).
  - 4 scheduled for tomorrow: `AIRLINE-MERGER` (Business, 07:30), `MARATHON-PREVIEW` (Sports, 10:00), `TENNIS-FINAL` (Sports, 11:00) and `RUGBY-SEMIFINAL` (Sports, 10:00, embargoed until 12:00).
  - 1 spiked (`HEALTH-WAITLIST`).
  - The rest saved and unpublished on their stages. `ELECTION-*` sluglines sit in the working stages of Politics, Business and World for the Master Desk filter shot.
- **4 pictures** in Sports / Incoming with headline, caption and alt text.
- **1 package** (`FESTIVAL-GUIDE`) on Culture / Working with two Culture stories.
- **Marks**: `SKIING-SEASON` and `ATHLETICS-TRIALS` marked for admin, `PENSION-REFORM` for marenholt.
- **Locks**: five stories open for editing by marenholt, tomasvidal (two), priyaraman and danielokafor, so Master Desk > Users shows lock counts.

### Settings and supporting data

Created after the newsroom, each block matched by name (or `_id`) on the next run. The comment above each block in `seed_data.py` names the documentation pages that need it.

- **Story content profile, body field** (`STORY_BODY`): every editor3 formatting option the writing and collaboration pages describe (including comments, suggestions, annotation and custom blocks) and a maximum length of 2000 characters, so the body shows its character count and limit.
- **Custom blocks** (`CUSTOM_BLOCKS`): `Fact box` and `Read more`, vocabularies with `field_type` `editor-block` and a short template.
- **Picture in a story body** (`BODY_MEDIA`): the picture `Kestrel Cup regatta, day three` after the first paragraph of OLYMPICS-SWIMMING, with a caption. It is written as association `editor_0`, as a MEDIA entity in `fields_meta.body_html.draftjsState` (editor3 reads the body from there once the profile has media blocks) and as an embed in `body_html`.
- **Crop sizes** (`CROP_SIZES`): `16-9` (1280x720) next to the snapshot's `4-3`, so the media editor offers Edit crops.
- **Dictionary** (`DICTIONARY`): an active `English` dictionary (`en`) built from every word in `seed_data.py` plus `/usr/share/dict/words` when that file exists, so seeded stories show no false spelling warnings. The server only turns `content_list` into words on PATCH, so it is created empty and then patched.
- **Templates** (`TEMPLATES`): the snapshot's `kill` and `takedown` templates get the headlines `KILL NOTICE` and `TAKEDOWN NOTICE` and a one-line body instead of `FIXME`.
- **Recent templates** (`RECENT_TEMPLATES`): the personal template `Election results brief` and the Politics desk template `Council meeting report`, written into admin's `templates:recent` preference for Politics, so the Create menu shows "Recent templates" (one with the **Private** tag). The server stores template names in lower case, so the menu lists them that way. The preferences resource is addressed by session id, so the seed writes it through its own admin session.
- **Desk settings** (`DESK_SETTINGS`): Politics gets the desk email `politics@meridian.example` and preferred categories Politics and National (stored with qcode and name, as the client stores them: bare qcodes show as empty chips in the desk settings); the categories vocabulary gets "Available in user/desk preferences" (`preffered_items`, spelled as on the server).
- **Workspace** (`WORKSPACES`): `Election night`, owned by admin, next to the snapshot's `Workspace 1`.
- **Personal items** (`PERSONAL_ITEMS`): `FERRY-NOTES` and `BUDGET-IDEAS` in admin's Personal space.
- **System messages** (`SYSTEM_MESSAGES`): `Planned maintenance tonight` (warning), `New election desk` (primary) and `Wire feed delayed` (alert). An active message is a toast at the top of every page, so all three stay inactive unless the seed runs with `--system-message-on`, which activates the first one. Run the seed with the flag right before the system-messages shots and without it right after.
- **Production API keys** (`API_KEYS`): `Mobile reporting app` (ARCHIVE_READ, DESKS_READ) and `Invoicing system` (USERS_READ). The generated secrets are not printed.
- **AI providers** (`AI_PROVIDERS`): `OpenRouter` (active) and `Newsroom local model` (inactive). Creating a provider does not contact it.
- **Products and subscribers** (`PRODUCTS`, `SNAPSHOT_SUBSCRIBER`, `SUBSCRIBERS`): product `General news` (both). `Subscriber 1` from the snapshot gets it in `products` and `api_products` and one Content API token (365 days). New subscribers: `Content API client` (Content API only, no destinations) and `Meridian Online` (digital, email destination like the snapshot subscriber, so publishing to it succeeds against the e2e mail service).
- **Saved searches** (`SAVED_SEARCHES`): `Election coverage` (private, admin), `Sports results` (global, admin, admin subscribed daily at 08:00) and `Budget watch` (global, marenholt). The snapshot's global `Malaysia` search is deleted (`SNAPSHOT_SAVED_SEARCHES_REMOVED`).
- **Highlights** (`HIGHLIGHTS`, `HIGHLIGHT_MARKS`): `Top Stories` (now/d) and `Election Watch` (now/w) on Politics. COUNCIL-TRANSIT is marked for both (double star), MINISTER-RESIGNS for Top Stories. ELECTION-BUDGET is deliberately left unmarked: a marked item shows a star in its authoring header, and many pages open that story. The server toggles marks, so only missing ones are posted.
- **Content lists** (`CONTENT_LISTS`, `CONTENT_LIST_WEBHOOKS`): `Homepage top stories` (limit 5, seven items, MINISTER-RESIGNS pinned at position 0), `Business briefing`, `Election special`, `Weekend sport` and the disabled `Culture picks`; then two webhooks to `.example` hosts (one disabled, excluding Culture picks). A list that already has items is left alone.
- **Availability** (`AVAILABILITY_TAGS`, `AVAILABILITY`, `AVAILABILITY_OVERRIDES`): the `availability_manager_tags` vocabulary ("Regions", North and South Aldmark with their towns), which the availability-manager extension needs to start; a default week for the six seeded users and admin (`PUT /default_user_availability/<user>`, which generates the next 12 weeks); and tomasvidal's entry for tomorrow set to unavailable by admin, so it shows "Modified by".
- **Comments** (`COMMENTS`): marenholt on PENSION-REFORM and tomasvidal on COUNCIL-TRANSIT, both mentioning `@admin`, which gives admin two unread notifications.

Schedule and embargo times are wall-clock times in `NEWSROOM["timezone"]` (Europe/London, the e2e server's `DEFAULT_TIMEZONE`) relative to the day you run the script.

## Resetting

`python3 seed.py --api-url http://localhost:5002/api --reset` is best effort:

- Seeded items are unlocked, unmarked and descheduled, then every unpublished one is spiked. Published items stay where they are.
- Seeded users lose their default desk and are disabled.
- Desks are deleted only when the server allows it, which in practice means never once they hold items. Sports gets its original members back and its explicit monitoring groups removed.
- The `Editor` and `Journalist` roles are deleted only when no user has them, which the disabled seeded users still do.
- The categories vocabulary goes back to the snapshot's placeholders.

- Content lists and webhooks, highlights, seeded saved searches, system messages, API keys, AI providers and the workspace are deleted. The Story profile, templates, vocabularies (custom blocks, crop sizes, availability regions), the dictionary, products and subscribers, availability entries and comments stay: restore the snapshot to undo them.

Running the seed after a reset restores everything: disabled users are enabled again and spiked items are unspiked back to their stage. For a truly clean instance, restore the snapshot with the `restore_record` call above.

## What it cannot do through the API

- **Planning assignments.** The e2e server does not install superdesk-planning, so there is no assignments resource. The Master Desk Assignments tab, the assigned counts on the Users tab and any planning items need a stack with planning enabled.
- **Remove published items, desks with content, users or roles.** Superdesk has no delete for archive items, refuses to delete desks that hold or once held items, only disables users, and refuses to delete roles that users still have. Use `restore_record` instead.
- **Keep locks alive on its own.** A lock belongs to the session that took it. Logging out that user, or the session expiring (`SESSION_EXPIRY_MINUTES`, 240 minutes of inactivity by default), releases it. Run the script again to lock the items again.
- **Client-side state.** Monitoring view (list, compact, swimlane, photo grid), monitoring filters (localStorage `sd-filter-*`), the preview pane, the Master Desk desk selection (`masterdesk:desks` preference) and the preferred desks in Send To are UI state. Set them in the capture steps.
- **Client config.** The "Marked for me" button and the "Marked for this user" section only show when the client loads the `markForUser` extension (the superdesk host build does; the stock e2e client does not, the patched one in CAPTURE.md does). The marks are stored either way. The same goes for `customAuthoringTopbar`, `list` settings and `monitoring.scheduled`.
- **Change the snapshot items.** `story 2` and `test sports story` stay unpublished because most shots need them that way. The scheduling shots that ask for them to be scheduled can use the seeded `MARATHON-PREVIEW`, `TENNIS-FINAL` and `RUGBY-SEMIFINAL` instead.
- **Real photography.** Generated pictures are simple illustrations. Pass `--images-dir` with real photos when the photo grid is the subject of the shot.
- **Keep schedules in the future.** They are set for "tomorrow" at seed time. If the capture happens later, restore the snapshot and seed again.

## Verified against a live server

The full seed, including the settings and supporting data above, has run against the client-core e2e stack on slot 1 (API http://localhost:5011/api) after a `main` snapshot restore, and a second run only logs `skip` lines. The capture setup for that stack is in `CAPTURE-STATUS.md`.

## The Planning stack: `seed_planning.py`

The Planning pages and the Master Desk Assignments tab are captured on the docs instance with the `autodocs-planning` snapshot (`FRESH=1 SNAPSHOT=autodocs-planning ./run-capture-autodocs.sh <page>/<shot>`). The superdesk-planning e2e stack (slot 1: client http://localhost:9021, API http://localhost:5021/api, `DEFAULT_TIMEZONE` Australia/Sydney) is the fallback and the setup the rest of this section describes. That stack has no `restore_record`; it is reset with the `planning_prepopulate_data` prepopulate profile instead. `seed_planning.py` does that reset and seeds on top of it (standard library only, data at the top of the script):

```bash
python3 seed_planning.py --api-url http://localhost:5021/api --reset   # wipe and seed
./run-capture-planning.sh superdesk-planning-component                 # capture (re-runs the seed first)
python3 seed_planning.py --scenario multilingual                       # then multilingual-event
python3 seed_planning.py --scenario grouped-preview                    # then planning-preview-groups
python3 seed_planning.py --reset                                       # back to the default profiles
```

- **Users and desks**: the profile's users get fictional names (logins unchanged, password `admin`); "Sports Desk" and "Politic Desk" become Sports and Politics, Business, World and Culture are created, "XEditor3 Desk" is deleted. The content profile and template are renamed Story; the Sports desk gets a "Weekly advisory" article template.
- **Planning data**: three events (two today, one tomorrow), four planning items for today and tomorrow (with text, picture and video coverages), five more dated yesterday so every desk has assignments in the states assigned, in progress and completed without adding rows to today's list. Work is started and completed through `assignments/content` and `assignments/complete`, logged in as the assignee.
- **Vocabularies for the full client**: the broadcasting vocabularies (`rundown_item_types` and the others from `seed_broadcasting.py`) and `availability_manager_tags`, because the client on the docs instance does not start without the first and shows administrators a blocking modal without the second. The planning e2e stack does not load those extensions.
- **Administration data**: agendas (one disabled), three event templates, the saved filter "Sport events this week", two custom layouts, three locations, the languages, countries and regions vocabularies, and today's featured stories list.
- **Clean-up on every run**: item locks, the Featured Stories lock and editor autosaves left by earlier captures are released or deleted (`run-capture-planning.sh` runs the seed without `--reset` before capturing; set `NO_SEED=1` to skip that).
- `--scenario` stores a partial event or planning profile that changes the editor for every shot, so it is applied only right before the shots that need it. The API cannot delete a profile override, so `--reset` is what undoes it.

Times are Sydney wall-clock times relative to the Sydney date when the script runs: seed and capture on the same Sydney day (Sydney midnight is 13:00 or 14:00 UTC). Without `--reset` the script skips what already exists (events and planning items by fixed guid, everything else by name).

## Broadcasting: `seed_broadcasting.py`

The Broadcasting page (`broadcasting-shows-and-rundowns`) needs a server with `apps.rundowns` and a client that loads the `broadcasting` extension. On the client-core stack that takes the patch in CAPTURE.md, "Broadcasting on the e2e stack". `seed_broadcasting.py` fills it (standard library only, data at the top of the script, same login and options as `seed_planning.py`):

```bash
python3 seed_broadcasting.py --api-url http://localhost:5011/api   # after seed.py, on the same day as the capture
python3 seed_broadcasting.py --dry-run                              # print the plan, no requests
```

- **Vocabularies**: `rundown_item_types` ("Item Type": Intro, Report, Live, Interview, Weather, Outro, each with a colour), `rundown_subitem_types` ("Subitem Type": Graphics, Lower third, Video wall), `rundown_item_status` (pending, in approval, approved, the default colours) and `camera` (K1, K2, K3). The superdesk host repo seeds these from `server/data/vocabularies.json`; the e2e snapshot has none of them, and the client cannot draw a rundown without them. When a vocabulary exists with other values, the seed replaces its values with these. The item type codes avoid `PRLG` and `AACC`, which get a different technical title on the server.
- **Shows**: `Meridian Tonight` (code MT, "Evening news bulletin", 30 minutes) and `Morning Briefing` (code MB, 15 minutes).
- **Rundown templates**: `Weeknight edition` for Meridian Tonight (air time 19:00, 30 minutes, air date today, name "Meridian Tonight // DD/MM/YYYY", automatic creation with Mon to Fri selected in the editor and 12 hours before air time, items Opening headlines, Weather and Closing) and `Weekday morning` for Morning Briefing (07:00, 15 minutes, no automatic creation, three items). Each show has exactly one template, so the Create rundown dialog preselects it. The editor numbers weekdays from Sunday (0) and the server's rrule from Monday (0), so the stored `by_day` `[1, 2, 3, 4, 5]` shows as Mon to Fri but would make the server create rundowns Tuesday to Saturday. The e2e stack runs no Celery beat, so nothing is created automatically either way.
- **Rundowns**, created from the templates through `POST /rundowns` as the Create rundown dialog does: `Meridian Tonight // <yesterday>` and `Morning Briefing // <today>` with their template items, and `Meridian Tonight // <today>` with a nine-item running order: the three template items with status and camera, plus an election debate report (two subitems, three paragraphs of script, the item the search shot finds), a studio interview, a rates report with a graphic, a live link with a video wall (pending, running 60 seconds over), and two short reports. The items run 24 minutes against a planned 30, so the Duration label is orange.
- **Locks**: every run releases rundown and rundown item locks left behind by a capture that did not close the rundown (it takes the lock over first, as the Unlock button does).

Rundown names carry the date in the client's `view.dateformat` (DD/MM/YYYY on the e2e client); the date format of a template must be one the template editor offers for that client format. Without `/api/shows` (no `apps.rundowns`) the script logs a `skip` line and exits without changes. Every run is idempotent: shows, templates and rundowns are matched by name, rundown items by title inside their rundown. A snapshot restore removes everything, so run it again after `seed.py`. The rundowns are dated relative to the day the script runs: seed again on the day of the capture.
