# Writer brief: Superdesk user guide refresh

You are writing one page of the official Superdesk user guide (GitBook, https://docs.superdesk.org/user-guide). The guide has not been updated since Superdesk 1.33 (2020). You write for journalists, editors and newsroom admins, not developers.

## Inputs

- Gap matrix (feature rows, page audit, new page scopes, resolved questions): `/Users/eos87/code/SourceFabric/Superdesk/Core/superdesk-docs-user-guide/tools/work/gap-matrix.md`. Read Sections C and E fully and every Section A row assigned to your page.
- Feature checklist 2.0 to 3.5 (for version numbers and marketing wording only): `superdesk-changelog-2.0-to-3.5.md` (same folder as the matrix).
- Develop delta after 3.5: `develop-delta.md` (same folder as the matrix).
- GitBook markdown reference: `/Users/eos87/code/SourceFabric/Superdesk/Core/superdesk-docs-user-guide/tools/work/gitbook-skill/write-docs.md`. Read it before writing.
- The docs repo (GitBook git sync of the user guide, local clone, branch `hg/user-guide-update`): `/Users/eos87/code/SourceFabric/Superdesk/Core/superdesk-docs-user-guide`. Pages live under `superdesk-user-guide/`, images under `.gitbook/assets/`. `SUMMARY.md` is the table of contents. Read `README.md` and one or two existing pages (the Availability Management pages are the most recent) to match tone and markup.
- Code on the develop branch, for verifying behaviour, menu labels, field names, config flags and privileges:
  - `/Users/eos87/code/SourceFabric/Superdesk/Core/superdesk-client-core` (UI; extensions in `scripts/extensions/*`; Playwright specs in `e2e/client/specs/` are step-by-step scripts of real flows and are a good source for exact labels)
  - `/Users/eos87/code/SourceFabric/Superdesk/Core/superdesk-core` (backend, settings in `superdesk/default_settings.py`, privileges in `*/privileges*` and resource `privileges` dicts)
  - `/Users/eos87/code/SourceFabric/Superdesk/Core/superdesk-planning` (planning module, specs in `e2e/`)
  - `/Users/eos87/code/SourceFabric/Superdesk/Core/superdesk-analytics`
  The checked-out branch may differ from develop, so read with `git -C <repo> show origin/develop:<path>` and search with `git -C <repo> grep -n -i -E '<pattern>' origin/develop -- <path>`. Never check out, modify or commit anything in these repos.
- Confluence how-to pages pulled as plain text: `tools/work/wiki/` in the docs repo (index in `wiki/README.md`). Read the ones listed for your page in your task. They are a secondary source: most predate Superdesk 2.0, some describe customer setups (files prefixed `stt-`, `fidelity-`, `belga-`, `sdcp-`). Use them for flows, field names and the reasons behind a behaviour, then verify against develop; the code wins on any conflict. Never copy customer names or customer desk names.
- Jira tickets (SDESK-xxxx etc.) can be read with the `jira-pull` skill if a ticket id in the matrix would help; use it sparingly.

## Rules

1. Describe the product as it is on develop. Verify every claim about UI labels, menu paths, field names and behaviour in the code or the e2e specs. If you cannot verify something, write it in the draft inside an HTML comment `<!-- VERIFY: ... -->` instead of guessing. Never invent a menu path.
2. Mark versions. Under a heading that documents a feature added after 2.0 put one italic line: `*Available since Superdesk 2.8.*` Use the version from the matrix. For things that only exist on develop after the 3.6 rc, write `*Available since Superdesk 3.6.*`
3. Optional modules (AI widget, iMatrics, content lists, SAMS, video editor, predefined text fields, broadcasting) get an info hint at the top of their section: "This is an optional module. If you do not see it, ask your administrator." Describe the admin side (how it is enabled, config keys, privileges) in a short "For administrators" subsection at the end of the page, not inline.
4. Customer-specific products and names stay out. Features that landed in the generic repos (for example custom editor tags, Gmail label routing) are documented as generic optional configuration, with no customer named.
5. Do not mention authoring-react, Editor 2, Angular, React or any internal implementation. Document the default authoring UI. Do not mention Superdesk Publisher (deprecated).
6. Markup: GitBook flavoured markdown as in the reference. Use `{% stepper %}` / `{% step %}` for sequences of user actions, `{% hint style="info|warning" %}` for callouts, `<figure><img src="..."><figcaption>...</figcaption></figure>` for screenshots. Close every block. Plain `##` and `###` headings. Keep the page title as the single `#` heading on line 1. No frontmatter unless the existing page has it.
7. Screenshots are placeholders for now. Reference them as `<figure><img src="../../.gitbook/assets/<page-slug>/<shot-name>.png" alt="..."><figcaption><p>Caption</p></figcaption></figure>` (adjust the relative depth to the page's folder). Every placeholder must have a matching entry in the manifest (below). Reuse an existing image from `.gitbook/assets/` only if it still matches the current UI, and say so in the manifest.
8. Writing style: short sentences, second person ("you"), one idea per sentence, no marketing language, no em-dashes, no emoji. Steps say what to click and what happens. Admin-only content is labelled as such. Explain the why in one sentence when a behaviour is surprising.
9. Keep what is still correct in the existing page. Rewrite, do not append. Remove duplicated sections, leftover chatbot text, stale "as of 1.33" phrasing and links to superdesk.github.io.
10. Links to other guide pages are relative markdown links to the `.md` file in the repo. Link to the pages in Section C by their proposed path even if they do not exist yet, and list such links in your report.
11. Do not edit `SUMMARY.md` or any page other than yours. Report the SUMMARY change you need instead.


## Canonical paths for new pages (link to these exactly; all under `superdesk-user-guide/`)

| Page | Path |
|---|---|
| Logging in and single sign-on | `getting-started/logging-in-and-single-sign-on.md` |
| Your profile and preferences | `navigating-superdesk/your-profile-and-preferences.md` |
| Master Desk | `workspace-and-search/master-desk.md` |
| Sending, scheduling and publishing items | `content-management/sending-scheduling-and-publishing.md` |
| Updates, corrections, kills and takedowns | `content-management/updates-corrections-kills-and-takedowns.md` |
| Translating content | `content-management/translating-content.md` |
| System messages | `administration/system-messages.md` |
| Planning administration | `superdesk-planning-component/planning-administration.md` (the planning page becomes `superdesk-planning-component/README.md`) |
| Asset management (SAMS) | `integrations-and-advanced-features/asset-management.md` |
| Content lists | `integrations-and-advanced-features/content-lists.md` |
| AI features | `integrations-and-advanced-features/ai-features.md` |
| Analytics | `integrations-and-advanced-features/analytics.md` |
| Broadcasting: shows and rundowns | `broadcasting-shows-and-rundowns.md` (top level, after the planning section) |
| Keyboard shortcuts | `reference/keyboard-shortcuts.md` |

Pages already drafted on the branch (read them to avoid overlap and to link to them): Master Desk, Monitoring Tab, Sending, scheduling and publishing items.

## Corrections to the matrix found by earlier writers

- F-037 "publishing shortcuts" are the top-bar buttons from `features.customAuthoringTopbar`, documented on the publishing page, not keyboard shortcuts.
- F-043 "Copy and send to desk" is Send & duplicate with `preserveEmbargoAndSchedule`; documented on the publishing page.
- There is no "Send correction" tab; the tab is "Publish" and only the button says "Send correction".
- Monitoring filters are stored in the browser (localStorage), the list view choice is a server-side user preference (`monitoring:view`), and a desk's default monitoring view overrides it.
- Master Desk: the single desk view has no desk-switch dropdown on develop; the Assignments tab needs Planning.
- Embargo does not block publishing; subscribers filter embargoed items with the `embargo` filter condition.

## Deliverables

1. The page file in the docs repo at the path given in your task (overwrite the existing page, or create the new one). Nothing else in the repo changes.
2. A screenshot manifest at `/Users/eos87/code/SourceFabric/Superdesk/Core/superdesk-docs-user-guide/tools/screenshots/manifests/<page-slug>.json`, a JSON array of objects: `{ "file": "<page-slug>/<shot-name>.png", "caption": "...", "route": "<client route or menu path>", "user": "admin|editor|journalist", "preconditions": ["item X exists in desk Y", ...], "steps": ["click ...", "..."], "viewport": "1440x900", "crop": "full|element: <css or test id>", "highlight": "<what to call out, or none>", "notes": "..." }`. Be precise enough that a Playwright script can be written from it without reading your page.
3. Your final report, short: the page path, word count, number of screenshots, every `VERIFY` comment you left, links to not-yet-existing pages, the SUMMARY.md entry you need, and anything in the matrix you found to be wrong.
