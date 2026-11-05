# Capture status (client-core stack)

State of the screenshot pipeline for the pages captured on the superdesk-client-core e2e stack, as of 2026-10-14. The Planning pages use the planning stack and `run-capture-planning.sh` instead (SEED.md, "The Planning stack").

## The stack

- Worktree `Core/superdesk-client-core-docs` (origin/develop at 7e08bc457), e2e slot 1: client http://localhost:9011, API http://localhost:5011/api, server `DEFAULT_TIMEZONE` Europe/London.
- Its `e2e/client/index.js` carries an uncommitted patch that loads markForUser, annotationsLibrary and ai-widget (with canned answers). The exact code and the reasons some extensions are left out are in CAPTURE.md, "e2e client patch". Keep the patch; never commit it.
- Bring it up (or check it) from the worktree: `./e2e/scripts/e2e-up.sh --slot 1`. After changing `index.js`, add `--rebuild`: the script does not notice source changes.

## Commands

From the docs repo root:

```sh
# clean start: restore the snapshot, then seed (always both; a restore wipes the seed)
curl -X POST http://localhost:5011/api/restore_record -H 'Content-Type: application/json' -d '{"name": "main"}'
python3 tools/screenshots/seed.py --api-url http://localhost:5011/api

# capture one page, or a comma-separated list of page/shot
tools/screenshots/run-capture.sh highlights
tools/screenshots/run-capture.sh highlights/highlight-star,highlights/highlight-view

# style, copy the styled PNGs into .gitbook/assets/<page>/, set image widths
python3 tools/screenshots/style_all.py tools/screenshots/out/raw tools/screenshots/out/styled
cp tools/screenshots/out/styled/<page>/<shot>.png .gitbook/assets/<page>/
python3 tools/screenshots/apply_widths.py .
```

- Do not pass `--restore` to `run-capture.sh`: it restores the snapshot before the first shot and nothing seeds it again. Restore and seed by hand instead.
- Running `seed.py` again is always safe: it only creates what is missing, re-takes expired locks and switches an active system message off.
- `master-desk/assignments-tab` belongs to the planning stack; on this stack the Assignments tab does not exist. Name the other Master Desk shots explicitly when capturing that page here.
- Check each raw PNG against its caption before styling. A shot reported `ok` can still show the wrong item or state.

## What the seed provides

SEED.md lists everything. Beyond the newsroom (desks, users, 36 stories, pictures, a package, marks, locks) it now also seeds: the Story body formatting options (all editor3 options, custom blocks included) and a 2000-character limit, custom blocks `Fact box` and `Read more`, a second crop size, an English dictionary, a picture inside the body of OLYMPICS-SWIMMING, readable kill and takedown templates, Politics desk email and preferred categories, the `Election night` workspace, two Personal space items, three system messages, two Production API keys, two AI providers, the `General news` product with two extra subscribers and a Content API token on `Subscriber 1`, three saved searches (the snapshot's `Malaysia` search is removed), two highlights with marks, five content lists with two webhooks, availability regions and default weeks for seven users, and two @admin comments (two unread notifications).

Preconditions that the seed or the client patch now fulfil start with "Done by seed.py" or "Done by the e2e client patch" in the manifests, or say "seeded by seed.py". Do not create those objects again through the API: highlights, comments and translations would be duplicated.

## Manifests

### Captured

- `master-desk` (7 shots, not `assignments-tab`), `monitoring-tab` (10), `sending-scheduling-and-publishing` (8): recaptured on 2026-10-14 with the renamed stages, styled and copied into `.gitbook/assets`.

- `broadcasting-shows-and-rundowns` (8 of 9): captured on 2026-10-14 on slot 1 with the broadcasting patch (CAPTURE.md, "Broadcasting on the e2e stack") and `seed_broadcasting.py`, styled and copied into `.gitbook/assets`. Run `seed_broadcasting.py` after `seed.py` and again before a rerun: it releases rundown locks a failed run leaves behind and puts the rundown list back in order.

### Capturable now

Preconditions are met on this stack. Only the shots marked "smoke-tested" have actually been run; the others are expected to need the usual step fixes.

- `availability-management` (6; `day-view` smoke-tested). Take it on a weekday: weekend days show mostly Unavailable.
- `collaboration-tools` (7)
- `content-configuration` (13). `vocabulary-delete-blocked` changes the Story profile: run it last, then restore and seed.
- `content-lists` (7; `lists-overview` smoke-tested). The data is right, but step 2 of `lists-overview` fails: "Wait until every card shows its headline preview or 'No articles in this list'" is read as waiting for the text 'No articles in this list'. Replace it with a wait on `[data-test-id="content-list-card"]`.
- `creating-and-editing-content-items` (8). "Recent templates" in the create menu is UI state the seed cannot set.
- `defining-publishing-in-superdesk` (8)
- `desk-creation-and-desk-management` (13). The routing shots build on each other (widget added, routing started, routing stopped); run the manifest in order in one go.
- `edit-media-items` (7 of 8; `body-media-block` smoke-tested)
- `highlights` (6; `highlight-star` smoke-tested). COUNCIL-TRANSIT carries the double star, not ELECTION-BUDGET (see Conventions).
- `icons-and-user-experience` (7). `notifications-panel` marks the two notifications as read; run `top-bar` first.
- `ingesting-news-items-and-events` (3)
- `keyboard-shortcuts` (2)
- `logging-in-and-single-sign-on` (4)
- `metadata-and-fields` (2)
- `navigation` (6)
- `packages` (6)
- `searching-content-in-superdesk` (6)
- `spiked-items` (3)
- `superdesk-api` (3). `subscriber-content-api-tab` now targets `Content API client` (the first subscriber in the list is no longer `Subscriber 1`).
- `superdesk-glossary-and-terminology-guide` (1)
- `system-messages` (3). Run `python3 tools/screenshots/seed.py --api-url http://localhost:5011/api --system-message-on` first and the plain seed right after: an active message is a toast at the top of every page.
- `translating-content` (6). A chain: `authoring-header-translated-from` creates the French translation the later shots use, and `correction-notification` needs marenholt to publish it and admin to correct the original (steps or API, see the entry). Restore and seed before running the page again, or a second translation appears.
- `updates-corrections-kills-and-takedowns` (8). `unpublish-confirm` shows no related-items list (optional, not seeded). Never click Send Kill, Unpublish or Resend.
- `user-management-and-user-roles` (10)
- `writing-and-formatting` (6; `editor-toolbar`, `spellchecker-menu` and `custom-block-menu` smoke-tested). `custom-block-menu` is no longer skipped. In `spellchecker-menu` the typed misspelling lands inside a word ("recievedthis"); the shot still works but a cleaner caret position would read better. `custom-block-menu` logs that "the open dropdown" crop part was not found; check its crop.
- `your-profile-and-preferences` (8). Under `notifications` the per-type checkboxes only list Mark for user, because Planning is not installed here.
- `ai-features` (6 of 7; `ai-providers-list`, `headline-suggestions` and `ai-provider-form` smoke-tested). `ai-provider-form` answers the model list with the new `mockRoutes` field, which works, but its steps still need fixing: step 2 opens 'Newsroom local model' instead of 'OpenRouter', and step 5 ("Open the same popover again ...") has no known shape.
- `dashboards-and-widgets` (13 of 14). The widgets are added by the earlier entries and used by the later ones; run the manifest in order in one go. The saved-search entries use the global `Budget watch`, because a desk Dashboard only lists global saved searches and the seeded `Election coverage` is private.

### Skipped, with the reason in the entry's `skip`

- `analytics` (all 9): superdesk-analytics is not installed on this stack.
- `asset-management` (all 8): no SAMS service and no `superdesk.sams` server app, so the sams extension is not loaded.
- `broadcasting-shows-and-rundowns/search-matching-items`: the client's search query never reaches the server's nested rundown item search, so no item rows appear under a rundown (reason in the entry).
- `ai-features/imatrics-tags`: auto-tagging-widget is not loaded (it adds an empty IMATRICS header field to every authoring view, and its build rewrites a tracked file).
- `dashboards-and-widgets/ingest-stats-widget`: the ingest collection is empty and no ingest provider can fetch here.
- `edit-media-items/video-editor`: needs the video editor extension and a video server.

## Conventions learned so far

- Seed, then capture on the same day. Schedules and embargoes are set for "tomorrow" (Europe/London) at seed time; AIRLINE-MERGER publishes at 07:30 the next morning. Locks last as long as the locking users' sessions (240 minutes idle); run the seed again to re-take them.
- Run `run-capture.sh`, not `capture.mjs` with defaults: it sets the slot-1 URLs, the cached Chromium and `--timezone Europe/London`, which keeps typed dates and listed times in line with the seeded wall-clock times.
- ELECTION-BUDGET is the story most pages open in authoring. Keep it clean: no highlight marks (a marked item shows a star in the authoring header), no saved edits, and discard changes in cleanup. Highlights use COUNCIL-TRANSIT and MINISTER-RESIGNS instead.
- Highlights, the new comments and the availability data are visible in other shots: red highlight stars on COUNCIL-TRANSIT and MINISTER-RESIGNS in Politics lists, and four unread notifications on the bell.
- The snapshot's own desks Education, Finance and "Without members" appear in every full desk list (Master Desk's Select desks, Send to, Settings > Desks). The seed leaves them alone.
- The "Connected to Notification Server!" toast did not appear in any client-core capture so far. If it shows up, the pattern the planning run used works: `{"action": "wait", "target": "text=Connected to Notification Server!", "state": "hidden", "optional": true}` before the shot.
- `capture.mjs` now counts a page as rendered once the top bar (`[data-test-id="top-menu"]`) is visible, so extension pages without the Workspace Panel (Availability Management, Content lists) load.
- `mockRoutes` (CAPTURE.md) answers requests to services the stack cannot reach. Use it instead of pointing the stack at real services.
- Dry-run after editing a manifest: `node tools/screenshots/capture.mjs --manifests tools/screenshots/manifests --out /tmp/x --dry-run`.
