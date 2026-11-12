# Capturing raw screenshots

`capture.mjs` drives the Superdesk web client with Playwright and writes raw, unstyled screenshots from the JSON manifests (one manifest per docs page). Styling is a separate step (`style.py` / `style_all.py`, see README.md).

## Setup

The script loads Playwright with `createRequire` from a folder that has `node_modules/playwright`; it has no build step and no `NODE_PATH` to set.

- Without a client-core checkout (cloud agents, CI): `npm ci` and `npx playwright install chromium` in this folder (`package.json` pins the same Playwright version as the e2e stack, 1.61.0), then pass `--playwright-from .`; `run-capture-autodocs.sh` does that on its own when `node_modules/playwright` is here.
- Default location otherwise: `../../../superdesk-client-core/e2e/client` relative to this folder (the sibling checkout).
- Override with `--playwright-from <dir>` or `SUPERDESK_E2E_CLIENT=<dir>`.
- The browser revision has to match that Playwright version (1.61 wants Chromium revision 1228). `./e2e/scripts/e2e-up.sh` installs it; by hand it is `npx playwright install chromium` from `e2e/client`. If you only have another Chromium build around, pass it with `--executable-path` (or `CHROMIUM_PATH`).

Node 24 is assumed (plain ESM, no build step).

## Running

Bring the e2e stack up first (from superdesk-client-core: `./e2e/scripts/e2e-up.sh`), then:

```sh
node capture.mjs --manifests <manifest-dir> --out <raw-dir> --restore
```

Options:

- `--only <page>[/<shot>]`: limit the run, comma-separated, for example `--only master-desk,monitoring-tab/preview-pane`. The page slug is the folder part of the entry's `file` (`master-desk/overview-tab.png` is page `master-desk`, shot `overview-tab`).
- `--base-url` (default `http://localhost:9000`) and `--api-url` (default `http://localhost:5002/api`).
- `--restore` posts to `<api-url>/restore_record` once before the first shot, the same call as the e2e `restoreDatabaseSnapshot()`. `--snapshot <name>` picks the snapshot (default `main`).
- `--users <file>`: user map, see below.
- `--timeout <ms>`: per action, default 15000.
- `--timezone <tz>`: browser time zone, default Europe/Prague. Set it to the server's `DEFAULT_TIMEZONE` (Europe/London on the e2e stack): when the two differ, dates typed into the embargo and publish schedule fields can shift by a day and list times differ from the seeded wall-clock times.
- `--headed`, `--slow-mo <ms>`: to watch it work.
- `--dry-run`: no browser. Parses every manifest and prints how each step, crop and highlight was understood. Run this after editing a manifest.

Output:

- `<out>/<page>/<shot>.png`: the shot, at device scale factor 2.
- `<out>/<page>/<shot>.highlights.json`: `[{"box": [x, y, w, h], "label": "1" | null, "style": "outline" | "badge"}]`, in output pixels relative to the crop.
- `<out>/<page>/<shot>.meta.json`: `{"preset": "dialog" | "wide" | "default"}`. `wide` for full-page shots, `dialog` for element crops narrower than 60% of the viewport, `default` otherwise.
- `<out>/_failed/<page>/<shot>.png` and `.log` for failed shots: a full-page debug screenshot plus the step log and the browser console.

A summary table (page, shot, status, reason) is printed at the end. Exit code is 1 if any shot failed. A failed shot never stops the run.

## What happens per shot

1. The context for the entry's `user` is reused or created (Chromium, 2x, light scheme, reduced motion, en-US, `--timezone`) and logged in once through the login form.
2. The viewport is set, `TEST_APP_CONFIG` and the `clearLocalStorage` prefixes are applied, and the route is loaded with a full page load, so each shot starts from a clean client state. Server-side state (preferences, locks, items) is not reset; see limitations.
3. The e2e client's `<style>` that forces Arial and disables font smoothing is removed (an init script drops it as it is inserted, and it is removed again after load), then the script waits for `document.fonts.ready`.
4. Items the user has open for editing are closed through the opened-articles bar at the bottom of the screen (unsaved changes are discarded), so stray item titles stay out of the shots and earlier shots' locks are released. "Item Unlocked" notices and the first-run welcome modal are dismissed whenever they appear.
5. The steps run. Before the shot, the script waits until no loading placeholders are visible, then computes the crop and highlights. `cleanup` steps run last, even when the shot failed.

## Users

| manifest `user` | logs in as |
| --- | --- |
| `admin` | admin / admin |
| `editor` | samgamgee / samgamgee (Sub Editor role) |
| `journalist` | frodobaggins / frodobaggins (no privileges at all) |

Add or override entries in `users.json` next to the script (or `--users <file>`):

```json
{"editor": {"username": "samgamgee", "password": "samgamgee"}, "reporter": "frodobaggins"}
```

A string value means username and password are the same. An unknown `user` is tried as a literal username with the same password, with a warning.

## Manifest fields

Each manifest is a JSON array. Fields the writers already use:

- `file`: output path, `<page>/<shot>.png`.
- `route`: `#/...` or `/#/...` is a client hash route. A full `http(s)://` URL is used as is. Anything else (for example `Settings > Desks`) is treated as a menu path: a warning is logged and the shot starts from `#/workspace/monitoring`, so the steps have to navigate.
- `user`: see above. Defaults to `admin`.
- `viewport`: `"1440x900"` (the default) or `{"width": 1440, "height": 1100}`.
- `steps`: free text, see the grammar below. A step can also be a structured object (see "Structured steps").
- `crop`: `full`, or `element: <selector>` with the extras listed below, or an object.
- `highlight`: `none`, free text, or an array of selectors.
- `caption`, `preconditions`, `notes`: not read by the script.

Extensions understood by the script:

- `padding`: CSS pixels added around element crops, default 16. The padded box is clamped to the viewport.
- `mask`: array of selectors to paint over (for example avatars or timestamps). `maskColor` changes the colour, default `#D9D9D9`.
- `highlightStyle`: `"outline"`, `"badge"` or `"callout"` (an outline plus a numbered badge on the same box, written as two entries). Without it, callout is used when the highlight text mentions callouts, badge when it mentions numbers or badges. Badge labels are the 1-based position of the item in the highlight list, so they line up with numbered lists on the page even when an item could not be found.
- `appConfig`: object merged into the client config through the `TEST_APP_CONFIG` localStorage key, which `scripts/init.ts` reads at startup. This is how to get config the e2e client does not have, for example `{"list": {"compactView": {"firstLine": ["headline", "slugline"], "secondLine": []}}}` or `{"features": {"customAuthoringTopbar": {"toDesk": true, "publish": true}}}`. It is removed again for entries that do not set it.
- `badgeAnchor`: where badges go. `"above"` or `"below"` centres each badge just outside its control (written as the badge's `center` in the highlights JSON, which style.py honours); `"rows"` puts badges for controls in the upper half of the crop above them and the rest below, for two-row toolbars; `"top-right"` moves the default corner to the element's top-right. It applies to the badge of a `callout` as well (the outline keeps the full box). An array sets one anchor per highlight item in highlight order, `null` keeping the default corner, for example `["below", "below", "top-right", null]`. The script warns when a badge overlaps another badge or a highlighted control. Leave room in the crop (for example `expand`) so badges outside the controls stay in frame; when the controls sit flush against other UI, an `evaluate` step that adds a margin (see `icons-and-user-experience/top-bar` or `navigation/screen-overview`) opens an empty band for the badges.
- `clearLocalStorage`: array of key prefixes to remove before loading the route, for example `["sd-filter"]`.
- `restore`: `true` or a snapshot name. Restores the database before this shot and logs every user in again (a restore invalidates the sessions).
- `cleanup`: steps (same grammar) run after the shot, for example to switch the monitoring view back to List view. Failures there are warnings only.
- `skip`: `true` or a reason. The shot is reported as skipped and does not fail the run.
- `keepOpenItems`: `true` keeps the opened-articles bar as it is instead of closing every open item first.
- `mockRoutes`: `[{"url": "**/api/ai_providers/*/models", "method": "GET", "json": {...}}]`. Requests matching the Playwright glob `url` (and `method`, when given) are answered with `json` (or `body` with `contentType`, and `status`, default 200) instead of reaching the server, from before the route loads until after cleanup. For services the e2e stack cannot reach, such as an AI provider's model list.

### Selectors in crop, highlight and mask

Free-text crops and highlights are read with the same tokenizer as steps: `[data-test-id="..."]` runs, CSS words like `.sd-board` or `button.sd-navbtn`, `#id`, CSS in parentheses, and quoted text. A plain selector string (in `mask`, in a highlight array, or in a structured crop) is resolved as a test id first, then as CSS, then as text. `data-test-id=foo` and bare `foo` both mean the test id `foo`. `text=...` and `role=button:Name` are accepted too.

Crop text understands:

- `element: A plus B plus C`: the union of all parts. Only the first part is required; missing extra parts are logged and left out.
- `top 400px`: limit the height from the top of the element.
- `plus about 200px of toolbar to its left` (or right, above, below): extend that side.
- Prose in parentheses is ignored and logged.
- Named regions: `the open popover`, `the open view switcher dropdown`, `the item row` (the last article row the steps touched), `the open dropdown`. The full list is `ALIASES` in `steps.mjs`.

Structured crop: `{"element": "<selector>", "plus": ["<selector>"], "expand": {"left": 200}, "maxHeight": 400, "clipAbove": ["<selector>"]}`. `clipAbove` ends the crop at the top of an overlay that covers the element's lower edge, such as the opened-articles bar over a side panel. or `{"region": {"x": 0, "y": 0, "width": 600, "height": 500}}` in CSS pixels.

### Crop proportions

A crop's height should not be more than 1.3 times its width, unless the element is a dialog or a side panel. For narrow vertical elements (a sidebar icon, a toolbar column), expand the crop to the right or capture a `region` so the shot reads as a landscape or square image. Images are displayed at their CSS size on the docs page (a separate script writes the width attribute), so a 64 px wide crop shows at 64 px, which is useless: the surrounding context is what makes a small control legible. `capture.mjs` warns when a crop breaks the rule. Dialogs (`role="dialog"`, modals) and side panels at least 80% of the viewport height are exempt; set `"allowPortrait": true` on an entry to exempt it explicitly.

### Highlights

A `highlight` array may contain a nested array of selectors; that item becomes one box around all of them.

Highlight text is split on commas and "and". A leading instruction like `number or outline:` or `box around` is dropped. Each item is resolved separately; an item that cannot be found is logged and skipped. If nothing resolves, an empty list is written.

## Step grammar

Each step string is split into clauses before a verb (`, click ...`, ` and wait ...`, ` then open ...`). Quoted text, `[data-test-id=...]` selectors, CSS words and routes are recognised anywhere in a clause. A trailing `so ...` purpose clause is ignored. Parenthesised prose is ignored, but a selector inside parentheses is used when the clause names no other element. Every step and clause is logged with the shape it matched.

| Shape | Examples |
| --- | --- |
| goto | `Open #/master-desk`, `open /#/workspace/monitoring`. Skipped when the page is already on that route. |
| select desk | `select desk 'Sports'`. Same logic as `Monitoring.selectDeskOrWorkspace`. |
| open item | `Open 'story 2' for editing`, `Open 'x' with the item actions menu > 'Edit'`, `... from desk 'Sports'`. Hovers the row, actions menu, Edit; falls back to a double-click. |
| open Send to / Publish | `open the Send to / Publish panel on the 'Publish' tab` |
| open view switcher | `open the view switcher`, `click the view switcher toggle` |
| click / double-click | `click [data-test-id="x"]`, `Click the 'Apply Filters' button`, `click 'Edit' in [data-test-id="context-menu"]`, `click its [data-test-id="y"]`, `Click the last button ...: button.sd-navbtn containing i.icon-switches`, `click the tab with role=tab name 'Send to'` |
| hover | `Hover [data-test-id="x"] with text 'story 2'` |
| check / uncheck | `check its [data-test-id="multi-select-checkbox"]`, `In [data-test-id="stage-select"] check the radio 'Incoming Stage'` |
| fill | `Type 'election' in the input with name="slugline"`, `fill <field> with 'text'`, `Change the headline in [data-test-id="field--headline"] to 'new'` (editor3 fields are retried until they hold the text) |
| set date / time | `In [data-test-id="embargo"] set the date to tomorrow and the time to 12:00`. Dates use the client's `view.dateformat`; `today`, `tomorrow`, `in N days` or a literal. |
| choose | `choose 'Education'`, `pick 'Europe/London'`: tree-select option, option, menu item, native select, radio, button, then text. |
| tree select | `In [data-test-id="filter-contentProfile"] select 'Story', 'Brief'` |
| switches | `Turn on the switches for Politics and Sports` |
| ensure selected | `Make sure the 'Publish' tab is active`: clicks only when not already selected. |
| wait | `wait for [x] to be visible`, `wait until [x] contains at least one [y]`, `Wait for [x] to show 'text'`, `Wait until [x] is enabled`, `Confirm the 'Go To Desk' button is visible`, `wait for ... to disappear`. A wait with nothing concrete in it waits for the network to go idle. |
| wait for images | `wait for all thumbnails to finish loading` |
| press | `press Escape`, `press Control+A`, `close the menu` |
| scroll | `Scroll to [x]` |
| mouse away | `move the mouse away from the list` |
| condition | `if [x] does not show SPORTS, click it and click ...` |
| repeat | `do the same for 'story 2'` replays the previous step with its item name replaced. |
| note | `Do not ...`, `Keep ...`, `Leave ...`: logged, nothing done. |
| optional | A clause starting with `Optionally` is tried; failure is a warning, not a failed shot. |

Anything else falls through to a generic attempt: the element the clause names (selector, quoted text, or the words themselves as test id, button name or text) is clicked or hovered. It is logged as `NO KNOWN SHAPE` and counted as a warning. A clause with nothing to act on fails the shot rather than being skipped.

### Structured steps

When free text is not enough, a step can be an object. These go straight to the executor:

```json
{"action": "click", "target": "[data-test-id=\"publish\"]"}
{"action": "click", "target": "li.sd-list-item:has(.user-items--locked)", "nth": "first"}
{"action": "fill", "target": "field--headline", "value": "New headline"}
{"action": "treeSelect", "target": "filter-contentProfile", "value": ["Story", "Brief"]}
{"action": "wait", "target": "modal-confirm", "state": "visible"}
{"action": "openItem", "name": "story 2", "desk": "Sports"}
{"action": "sleep", "ms": 500, "optional": true}
```

Actions: `goto` (`route`), `click`, `dblclick`, `hover`, `check` (`value: false` unchecks), `fill`, `press` (`key`), `wait` (`state`: visible, hidden, enabled), `selectDesk`, `openItem`, `openSendPublish` (`tab`), `openViewSwitcher`, `choose`, `treeSelect`, `switches` (`names`, `on`), `scroll`, `mouseAway`, `waitImages`, `settle`, `sleep`, `evaluate` (`script`). `text` on any target adds a has-text filter.

## Lessons from the first live run

- `TEST_APP_CONFIG` replaces whole top-level blocks. Patching only `list.compactView` empties the normal list rows, so an `appConfig` that touches `list` must carry the full list config.
- The Send to / Publish panel saves embargo and schedule values to the item. Use a throwaway item and clear the dates in `cleanup`.
- Embargo and schedule dates are typed (the masked date field ignores `fill`), times are filled (native `type="time"` input).
- Styled radio and checkbox inputs (Master Desk tabs, stage radios, multi-select) are checked with `force`, because their label intercepts a real click.
- `data-test-value` on monitoring rows is the item's headline, not its slugline.

## Lessons from the docs instance

- Planning pages are captured on the docs instance with the `autodocs-planning` snapshot (`SNAPSHOT=autodocs-planning`, `FRESH=1` for shots that depend on today's dates), not on a local planning stack. The planning e2e stack is the fallback when the instance is down.
- The full client loads extensions the e2e stacks do not: broadcasting dereferences the `rundown_item_types` vocabulary while loading and the whole client dies without it (nothing renders after login, no error on screen), and availability-manager shows administrators an "issues with instance configuration" modal without `availability_manager_tags`, which swallows every click. `seed_planning.py` creates both sets of vocabularies and `dismissInterruptions` closes the modal.
- After a start with an empty database the instance seeds itself for a few minutes. A reseed from the laptop during that time wipes the seed under it; `run-capture-autodocs.sh` waits for the seed marker first.
- A 403 from the instance (nginx, not Superdesk) means the instance is gone or stopped, not rebuilding: a Fireq restart brings it back, and with an empty database it seeds itself again.
- Connections from a laptop to the instance stall for a minute or more now and then, with nothing in the server log. The seeds retry a stalled request three times; the login waits in `capture.mjs` grow with `--timeout`.
- The Assignments route shows the custom-workspace dropdown instead of the Desk Assignments / My Assignments buttons when the page is opened directly by URL, because Planning reads the active desk once at start-up. Select a desk on Monitoring first (`select desk 'Politics'`).
- The Playwright browser cache (`~/Library/Caches/ms-playwright`) can disappear between sessions; `npx playwright install chromium` from the e2e client folder puts the matching headless shell back.

## e2e client patch

The client-core e2e client (`e2e/client/index.js` in the worktree that builds slot 1, `Core/superdesk-client-core-docs`) is patched locally and the change is not committed, so it has to be reapplied after a fresh checkout. The full diff of that worktree (index.js, `e2e/server/settings.py`, `e2e/server/Dockerfile`, against client-core 7e08bc457) is saved as `client-core-e2e-docs.patch` next to this file; apply it with `git apply` in a fresh worktree. Slots 2 and 3 used worktrees `-docs2` and `-docs3` with a subset of the same patch; they were removed on 2026-10-22, so `run-capture-s2.sh` and `run-capture-s3.sh` need a worktree recreated before they run again. Stock, `startApp` loads availability-manager, content-lists and the publishing-sections test extension. The patch adds, between content-lists and publishing-sections:

- `markForUser`: `import('superdesk-core/scripts/extensions/markForUser')`. "Marked for me", "Mark for user" and the "Marked for this user" groups.
- `annotationsLibrary`: `import('superdesk-core/scripts/extensions/annotationsLibrary')`. The Annotations library page and tab in the annotation popup.
- `ai-widget`, with canned answers because the stack has no AI service:

```js
{
    id: 'ai-widget',
    load: () => import('superdesk-core/scripts/extensions/ai-widget').then((ext) => {
        ext.configure(() => ({
            generateHeadlines: () => Promise.resolve([
                'Coalition budget promises tax relief for 1.2 million households',
                'Election budget cuts family income tax and adds levy on holiday rentals',
                'Opposition questions how coalition will pay for pre-election tax cuts',
            ]),
            generateSummary: () => Promise.resolve('The governing coalition presented an election-year budget that cuts income tax for about 1.2 million households. Finance Minister Ilse Marrow said a new levy on short-term rentals and a freeze on defence spending would pay for it. The opposition Civic Union said the levy would raise less than half of the 900 million crowns the government expects.'),
            translations: {
                generateTranslations: () => Promise.resolve('<p>Die Regierungskoalition hat am Montag einen Wahlhaushalt vorgestellt, der die Einkommensteuer für rund 1,2 Millionen Haushalte senkt.</p><p>Finanzministerin Ilse Marrow sagte, die Entlastung werde durch eine neue Abgabe auf Kurzzeitvermietungen finanziert.</p>'),
                translateActionIntegration: false,
            },
        }));

        return ext;
    }),
},
```

Rebuild with `./e2e/scripts/e2e-up.sh --slot 1 --rebuild` from that worktree. Without `--rebuild` the script does not notice a changed `index.js`: it only rebuilds when the bundles are missing or were built for other backend URLs.

Not loaded, on purpose:

- `auto-tagging-widget` (iMatrics): it loads, but adds an empty IMATRICS field to the header of every authoring view, which would change every authoring screenshot in the guide. Its main file is compiled output, so the build runs `npm install && npm run compile` in the extension folder and then rewrites the tracked `scripts/extensions/auto-tagging-widget/package.json` (`correctMainPathInPackageJson` in build-tools).
- `sams`: the e2e server has no `superdesk.sams` (no `/api/sams/...`), so the pages would only show errors.
- `broadcasting` is loaded on slot 1 only, together with a server patch; see "Broadcasting on the e2e stack" below.
- `videoEditor`: needs a video server.

## Broadcasting on the e2e stack

The Broadcasting page needs a server part and a client part, and the stock e2e stack has neither. Slot 1 (`Core/superdesk-client-core-docs`) carries three more uncommitted changes for it; keep them out of any commit.

- `e2e/server/settings.py`: `INSTALLED_APPS = ["apps.rundowns"]` appended at the end (the e2e settings only list extra apps there, so this adds the rundowns resources, the `rundowns` privilege and the export formatters).
- `e2e/server/Dockerfile`: `fonts-dejavu-core` added to the `apt-get install` line next to `libmagic-dev`, for the PDF exports.
- `e2e/client/index.js`: in the `startApp` extension list, after availability-manager:

```js
{
    id: 'broadcasting',
    load: () => import('superdesk-core/scripts/extensions/broadcasting').then((broadcasting) => {
        broadcasting.setCustomizations({
            getRundownItemDisplayName: (rundown) => rundown.technical_title,
        });

        return broadcasting;
    }),
},
```

This is the same `setCustomizations` block as the superdesk host client, so rundown item rows show the technical title, as in a default installation.

`e2e-up.sh --slot N --rebuild` only rebuilds the client; it never rebuilds the server image. After changing the server files, rebuild the image and restart the slot from the worktree:

```sh
docker build -t superdesk-client-core-e2e-server:ci e2e/server
./e2e/scripts/e2e-down.sh --slot N
./e2e/scripts/e2e-up.sh --slot N
```

After changing `index.js`, `./e2e/scripts/e2e-up.sh --slot N --rebuild` (or, with the slot already running, `SUPERDESK_URL=http://localhost:50NN/api SUPERDESK_WS_URL=ws://localhost:51NN npm run build` in `e2e/client`, which is what the script runs). Check that the bundle has it: `grep -c "Manage Rundown Templates" e2e/client/dist/app.bundle.js` must print 1, and the Broadcasting icon must appear in the Workspace Panel. Then seed the data with `seed_broadcasting.py` (SEED.md). The image tag is shared by every slot, so the other slots pick the patched server up the next time they are recreated; that is harmless (the rundowns resources stay empty and the client of those slots does not load the extension).

## Known limitations

- The e2e client (port 9000 from `e2e-up.sh`, 901N on a slot) is not the default host build. Stock, it loads only the availability-manager, content-lists and publishing-sections extensions; see "e2e client patch" above for what the documentation build adds. Its config has no `list.compactView` and no `features.customAuthoringTopbar`, and superdesk-planning is not installed, so the Master Desk Assignments tab is hidden. Use `appConfig` for config gaps, or point `--base-url` at a host build that talks to the same backend.
- The `main` snapshot has no pictures, no scheduled items, no desks called Politics, Business or Culture, and no planning data. Run `seed.py` after every restore (SEED.md).
- A route counts as rendered once the top bar (`[data-test-id="top-menu"]`) or one of the workspace containers is visible, so extension pages without the Workspace Panel (Availability Management) load too.
- Steps change server-side state that survives the per-shot reload: user preferences (monitoring view, Master Desk desk selection), item locks from opening items, autosaved edits. Use `cleanup` steps, or `restore` on the entry that needs a clean state.
- `editor` maps to samgamgee, who lacks `send_to_personal` and `unlock`. Shots that need those actions should use `admin`.
- Hover-only UI (tooltips) is captured as it is at screenshot time. `animations: 'disabled'` finishes CSS transitions first, but a tooltip that renders outside the crop is cut off.
- Highlights from prose are best effort. Descriptions like "the selection count" or "the per-desk switches" resolve to nothing and are logged; use a selector in the manifest.
- Element crops are clamped to the viewport. An element taller than the viewport needs a taller `viewport`.
