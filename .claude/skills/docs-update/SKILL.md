---
name: docs-update
description: Update the Superdesk user guide for one merged product PR. Use when given a merged PR from superdesk-client-core, superdesk-core, superdesk-planning or superdesk-analytics (as owner/repo#number or a PR URL) and asked to reflect it in the docs. Decides whether the change is user-facing, edits the affected guide pages, recaptures screenshots on the docs instance and opens a docs PR for human review.
---

# Update the user guide for a merged PR

You turn one merged product PR into one docs PR, or into a short report saying no docs change is needed. The repo you are in is the GitBook git sync of https://docs.superdesk.org/user-guide. Pages live under `superdesk-user-guide/`, images under `.gitbook/assets/<page-slug>/`, screenshot manifests under `tools/screenshots/manifests/<page-slug>.json`. A human reviews every docs PR, so prefer a precise small change over a broad rewrite, and say what you were not sure about.

Input: the PR as `owner/repo#number` or a URL. Split it into `REPO=owner/repo` and `NUM=number` first. Use only `gh api` (REST) for GitHub, never `gh pr ...`: the cloud sandbox's GitHub proxy rejects GraphQL, which every `gh pr` subcommand uses, and `gh` also misreads `owner/repo#number` as a branch name. In the cloud the proxy answers API calls only for repositories attached to the session (the docs repo, superdesk, superdesk-client-core and superdesk-core are); if it refuses one, read that repo through git instead (`git clone --depth 300 --no-single-branch <url>` into a scratch folder, then `git log`, `git show`), note in the report that you could not read the PR body, and do not try to attach repositories yourself. If several PRs are given, handle each on its own branch.

## 0. Check the tools

Run these once, before anything else, and stop with a report if one fails:

- `gh auth status`, then `gh api repos/$REPO/pulls/$NUM --jq '{merged, merged_at, merge_commit_sha, title}'` (the PR must be merged; an open PR means stop and say so).
- `curl -fsS -m 20 "${AUTODOCS_URL:-https://sd-autodocs.test.superdesk.org}/api/"` (the docs instance).
- Playwright: `cd tools/screenshots && npm ci` on a fresh machine, then a browser. In the cloud sandbox Chrome for Testing is preinstalled and `CHROMIUM_PATH` points at it (the capture wrapper passes it to Playwright), so nothing to download. Elsewhere `npx playwright install chromium` there, or `--with-deps` as root on Linux. On a laptop with a superdesk-client-core checkout next to this repo, `E2E_CLIENT` (or `SUPERDESK_E2E_CLIENT`, the name `capture.mjs` reads) may point at its `e2e/client` instead. Read `tools/screenshots/CAPTURE.md` once.
- A private copy of the tools, so they keep working when the branch you edit later predates them (step 2 may put you on an older docs branch): `TOOLS=$(mktemp -d) && git archive HEAD tools .claude | tar -x -C "$TOOLS"`. Run `lint.py`, `sync_indexes.py`, `capture.mjs` and the capture wrapper from `$TOOLS` from here on; `npm ci` goes into `$TOOLS/tools/screenshots`. Manifest edits still go into the repo's `tools/screenshots/manifests/` when the branch has it; when it does not, put the manifest entry into the PR body for the reviewer.
- Lint baseline, before you edit anything: `python3 $TOOLS/tools/work/lint.py . > $TOOLS/lint-before.txt; true`. The guide carries known problems on pages you will not touch; you fix only what you add.

## 1. Decide whether the PR is user-facing

Read the PR: `gh api repos/$REPO/pulls/$NUM` (title, body, labels, `merge_commit_sha`, `merged_at`), `gh api repos/$REPO/pulls/$NUM/files --paginate --jq '.[].filename'` and the diff, `gh api repos/$REPO/pulls/$NUM -H 'Accept: application/vnd.github.diff'`. Follow linked tickets only if the PR body is empty (the `jira-pull` skill when it is available, otherwise skip). The body often names a dependent PR in another repo (`superdesk/superdesk-core#3347`, or a PR URL): read each one the same way, note its merge state, and carry it through steps 3 and 5, because the feature only exists on the instance when every part is there.

Not user-facing, report and stop without a branch or PR: dependency bumps, CI and tooling, tests and e2e specs, refactors and typing, performance work with no visible change, server internals with no new setting, privilege or UI text, fixes that restore documented behaviour (mention them in the report as "bug fix, docs already describe the intended behaviour").

User-facing, continue: new or removed UI (buttons, menus, panels, widgets, pages), changed labels or menu paths, new or renamed settings in `superdesk.config.js` or server settings that an admin would set, new privileges, changed defaults, new limits or validation errors on existing fields, new keyboard shortcuts, behaviour changes a journalist or admin would notice.

When you cannot tell, treat it as user-facing but keep the edit small and say in the PR why you were unsure.

## 2. Find the pages

Start from the files in the diff, then confirm by searching the guide text for the labels, setting names and feature names the diff touches: `git grep -n -i -E '<label|setting|feature>' -- superdesk-user-guide README.md`. The table lists the usual homes; the search wins when they disagree. Check the path exists (`git ls-files superdesk-user-guide | grep <name>`): the guide is being rewritten page by page and some pages below are still in open docs PRs. When a page is missing, put the content in the closest existing page and say so in the PR; do not create it. Also check whether an open docs PR rewrites the page: `gh api 'repos/superdesk/superdesk-docs-user-guide/pulls?state=open' --jq '.[] | "\(.number) \(.head.ref)"'`, then `gh api repos/superdesk/superdesk-docs-user-guide/pulls/<n>/files --jq '.[].filename'` for each. If one does, branch from that PR's head instead of `main`, edit the page as it is there, open your PR with `--base <that branch>`, and say so in the PR body; editing the `main` version would build on text that PR replaces.

| Code area (superdesk-client-core unless noted) | Guide pages (under `superdesk-user-guide/`) |
| --- | --- |
| `scripts/apps/monitoring`, `scripts/apps/workspace`, `scripts/apps/dashboard` | `workspace-and-search/monitoring-tab.md`, `workspace-and-search/desks-and-custom-workspaces.md`, `workspace-and-search/dashboards-and-widgets.md` |
| `scripts/apps/search`, `scripts/apps/search-providers` | `workspace-and-search/searching-content-in-superdesk.md` |
| `scripts/apps/master-desk` | `workspace-and-search/master-desk.md` |
| `scripts/apps/highlights` | `workspace-and-search/highlights.md` |
| `scripts/apps/authoring`, `scripts/apps/authoring-react`, `scripts/apps/fields`, `scripts/apps/relations` | `content-management/creating-and-editing-content-items/*.md` |
| `scripts/apps/publish`, `scripts/apps/publish-preview`, `scripts/apps/internal-destinations` | `content-management/sending-scheduling-and-publishing.md`, `content-management/updates-corrections-kills-and-takedowns/*.md`, `administration/defining-publishing-in-superdesk.md` (or `.../defining-publishing-in-superdesk/*.md`) |
| `scripts/apps/archive` (spike, duplicate, send) | `content-management/spiked-items.md`, `content-management/sending-scheduling-and-publishing.md` |
| `scripts/apps/packaging` | `content-management/packages.md` |
| `scripts/apps/translations` | `content-management/translating-content.md` |
| `scripts/apps/desks`, `scripts/apps/users`, `scripts/apps/settings` | `administration/desk-creation-and-desk-management.md`, `administration/user-management-and-user-roles.md` |
| `scripts/apps/vocabularies`, `scripts/apps/templates`, `scripts/apps/content-filters`, `scripts/apps/dictionaries`, `scripts/apps/products` | `administration/content-configuration.md` (or `.../content-configuration/*.md`), `administration/defining-publishing-in-superdesk.md` |
| `scripts/apps/system-messages` | `administration/system-messages.md` |
| `scripts/apps/ingest` | `integrations-and-advanced-features/ingesting-news-items-and-events.md` |
| `scripts/apps/content-api`, `scripts/apps/production-api-keys` | `integrations-and-advanced-features/superdesk-api.md` |
| `scripts/apps/ai-providers`, `scripts/extensions/ai-widget`, `scripts/extensions/auto-tagging-widget` | `integrations-and-advanced-features/ai-features.md` |
| `scripts/extensions/content-lists` | `integrations-and-advanced-features/content-lists.md` |
| `scripts/extensions/sams` | `integrations-and-advanced-features/asset-management.md` |
| `scripts/extensions/broadcasting` | `broadcasting-shows-and-rundowns.md` |
| `scripts/extensions/availability-manager` | `availability-management/*.md` |
| `scripts/extensions/markForUser`, `scripts/extensions/usageMetrics`, `scripts/extensions/predefinedTextField`, `scripts/extensions/videoEditor` | `workflow-tools/*.md`, `content-management/creating-and-editing-content-items/*.md` |
| keyboard shortcut changes anywhere | `reference/keyboard-shortcuts.md` |
| superdesk-planning | `superdesk-planning-component/*.md` (or `superdesk-planning-component.md`) |
| superdesk-analytics | `integrations-and-advanced-features/analytics.md` |
| superdesk-core settings, privileges, publish and ingest behaviour | the page that documents the feature, usually its "For administrators" section |

A new page is the exception: only for a whole new feature that has no home, and then it goes into `SUMMARY.md` and `python3 tools/work/sync_indexes.py .` regenerates the section lists.

## 3. Ground every claim in the code

Labels, menu paths, field names, setting keys and privilege names come from the merged code, not from the PR description. Read the changed files on the merge commit (`gh api repos/$REPO/contents/<path>?ref=<mergeCommit> -H 'Accept: application/vnd.github.raw+json'` or a shallow clone). Never write a menu path you have not seen in the code or an e2e spec. If something can only be checked on a running instance, check it on the docs instance: a scratch manifest outside the repo with the steps to reach the state and `MANIFESTS=<dir> OUT=<dir> bash $TOOLS/tools/screenshots/run-capture-autodocs.sh <page>/<shot>` gives you a screenshot to look at without touching the repo's manifests. If that is not possible leave a one-line `<!-- VERIFY: what to click and what to look for -->` comment and list it in the PR; the strict lint refuses such comments, so the PR goes up as a draft.

Version line: a feature added after the last release gets one italic line under its heading, `*Available since Superdesk X.Y.*`. Find the newest release branch of the product repo: `gh api repos/$REPO/branches --paginate --jq '.[].name' | grep '^release/' | sort -V | tail -1`, giving `release/X.Y`. If the merge commit is also on that branch (`gh api repos/$REPO/compare/release/X.Y...<mergeCommit> --jq .status` is `behind` or `identical`), the version is X.Y; otherwise it is the next minor, X.(Y+1). A change to an existing feature gets no version line.

## 4. Edit the pages

Style and markup, from `tools/work/writer-brief.md` (rules 1, 3 to 6, 8 and 9; the other rules there belong to the manual refresh and do not apply here) and `tools/work/gitbook-skill/write-docs.md` for GitBook syntax:

- Second person, short sentences, one idea per sentence. Steps say what to click and what happens. No marketing language, no em-dashes, no emoji.
- `{% stepper %}` / `{% step %}` for sequences of actions, `{% hint style="info|warning" %}` for callouts, every block closed. Plain `##` and `###` headings, the page title stays the single `#` on line 1.
- Figures: `<figure><img src="../../.gitbook/assets/<page-slug>/<shot>.png" alt="..."><figcaption><p>Caption</p></figcaption></figure>`, relative depth adjusted to the page's folder, and a matching manifest entry.
- Optional modules get the info hint "This is an optional module. If you do not see it, ask your administrator." at the top of their section; admin setup goes into the page's "For administrators" section, not inline.
- No customer names, no implementation names (React, Angular, authoring-react, Editor 2), no Superdesk Publisher, no links to superdesk.github.io.
- Links to other guide pages are relative links to existing `.md` files only.

Edit only the pages the change affects. Rewrite the affected sentences in place rather than appending a "new in" paragraph. Remove what the PR made wrong. On a page that still has the old guide's style (third person, upper-case field names), your sentences follow the rules above but keep the page's own terms and labels; do not restyle the rest of the page, and apply the cleanups of rule 9 only to sentences you rewrite anyway.

## 5. Screenshots

A figure needs recapturing when the PR changed what it shows, and a new figure is justified when the text describes a control the reader has to find. Error and validation states get no figure; the text names the message. Everything else keeps its image.

The docs instance (`https://sd-autodocs.test.superdesk.org`, admin / admin) is built from the `auto-docs` branch of `superdesk/superdesk`. Check that the instance already has the merged change before capturing, for `$REPO` and for every dependent PR from step 1:

- Client packages (superdesk-client-core, superdesk-planning, superdesk-analytics client side) are pinned by `client/package-lock.json` on that branch (Fireq runs `npm ci`):

  ```sh
  PIN=$(gh api -H 'Accept: application/vnd.github.raw+json' "repos/superdesk/superdesk/contents/client/package-lock.json?ref=auto-docs" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["packages"]["node_modules/<package>"]["resolved"].split("#")[1])')
  gh api "repos/$REPO/compare/<mergeCommit>...$PIN" --jq '.status'
  ```

  `<package>` is `superdesk-core` for superdesk-client-core, else `superdesk-planning` or `superdesk-analytics`. `ahead` or `identical` means the instance has the change; anything else means it does not.
- Server packages (superdesk-core, superdesk-planning, superdesk-analytics server side) are installed from the git ref in `server/requirements.txt` on that branch, with no lock: `gh api -H 'Accept: application/vnd.github.raw+json' "repos/superdesk/superdesk/contents/server/requirements.txt?ref=auto-docs" | grep -o '<repo-name>.git@[^ ]*'` gives the ref. If it is a commit or a branch other than `develop`, run the same `compare/<mergeCommit>...<ref>` check. If it is `develop`, the instance has the change when the last push to `auto-docs` (`gh api repos/superdesk/superdesk/commits/auto-docs --jq .commit.committer.date`) is later than the PR's `mergedAt`.

When the instance is behind, do not capture: leave the figure in the text with `<!-- SCREENSHOT PENDING: needs $REPO <mergeCommit> on the docs instance -->` on the line before it, make sure the manifest entry is right, and say in the PR that the shot waits for the instance. Someone re-runs this skill for the same PR once the instance has moved; a re-run on an existing `docs-update/*` branch continues that branch (step 7).

Capture, one shot or one page at a time, never two runs at once (the capture users share locks):

1. Add or adjust the entry in `tools/screenshots/manifests/<page-slug>.json` (fields and the step grammar are in `CAPTURE.md`; copy the shape of a neighbouring entry). `cd $TOOLS/tools/screenshots && node capture.mjs --manifests <repo>/tools/screenshots/manifests --out out/raw --dry-run --only <page>/<shot>` must parse it cleanly (the manifests are read from the repo, the output stays in the scratch copy).
2. `MANIFESTS=<repo>/tools/screenshots/manifests bash $TOOLS/tools/screenshots/run-capture-autodocs.sh <page-slug>/<shot>`. Use `SNAPSHOT=autodocs-planning` for Planning pages and `FRESH=1` when the shot depends on today's date or on a lock. A failed shot leaves `out/raw/_failed/<page>/<shot>.png` and `.log`; fix the steps and run again, at most three attempts, then leave the figure pending as above. A 5xx or a connection error means the instance is restarting (every push to `auto-docs` rebuilds it): wait two minutes and retry, up to twenty minutes, and those retries do not count as attempts.
3. Look at the raw PNG before accepting it: the right screen, nothing unrelated open, the highlighted control is the one the text names.
4. In `$TOOLS/tools/screenshots`: `python3 style_all.py out/raw out/styled`, copy `out/styled/<page-slug>/<shot>.png` to the repo's `.gitbook/assets/<page-slug>/`, then `python3 apply_widths.py <repo>` so the figure gets its display width.

Never commit `tools/screenshots/out/`, `node_modules/`, scratch files or `package-lock.json` changes you did not mean; `git status` must show only the pages, images and manifests you meant to change before you commit. Never change the instance's data by hand; a restore (`run-capture-autodocs.sh` does it) is the only reset you use.

## 6. Check

From the repo root: `python3 $TOOLS/tools/work/lint.py . > $TOOLS/lint-after.txt; diff $TOOLS/lint-before.txt $TOOLS/lint-after.txt` (the output is sorted, so the diff shows only what you changed). Fix every problem on lines you added or changed, leave the pre-existing ones alone and list them in one line of the PR body. Then `python3 $TOOLS/tools/work/lint.py . --strict <changed pages>`: it fails on pending shots, kept VERIFY comments and on old problems of a touched page alike; whenever it fails, the PR is a draft.

## 7. Open the docs PR

- Branch from `main`: `docs-update/<repo-short>-$NUM` (for example `docs-update/client-core-5123`). If that branch already exists on origin (a re-run), check it out, rebase it on `main` only if it is clean to do so, continue on it and update the open PR instead of opening a new one.
- One commit, authored by the bot, not by Claude: `git -c user.name=superdesk-docs-bot -c user.email=352859303+superdesk-docs-bot@users.noreply.github.com commit ...`. Title `[<TICKET>] <Imperative summary of the docs change>` when the product PR title carries a ticket id in brackets, otherwise without the prefix. Reference the product PR in the body as `superdesk/superdesk-client-core#5123`, not in the title. No co-author trailers. On a re-run, a second commit is fine.
- `git push -u origin <branch>`, then create the PR over REST, with `draft` true when anything is pending: `gh api repos/superdesk/superdesk-docs-user-guide/pulls -f title="<commit title>" -f head=<branch> -f base=main -F draft=true -f body="$(cat <file>)" --jq .html_url`. On a re-run with an open PR, edit it instead: `gh api -X PATCH repos/superdesk/superdesk-docs-user-guide/pulls/<n> -f body=...`. Write the body to a file first, short and plain:
  - the product PR link and one or two sentences on what changed for users
  - the pages touched
  - shots recaptured, added, or pending (with the reason)
  - what the reviewer should check (VERIFY lines, pre-existing lint problems, anything you were unsure about)
- Never push to `main`.

## 8. Report

End with: the decision (user-facing or not, why), the docs PR URL or "no PR", pages and figures changed, anything pending, and what a human has to do next. Keep it under fifteen lines.
