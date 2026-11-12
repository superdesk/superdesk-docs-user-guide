# Review brief: Superdesk user guide refresh (pass 1, 2026-10-13)

You review one or more pages of the rewritten user guide on branch `hg/user-guide-update` of `/Users/eos87/code/SourceFabric/Superdesk/Core/superdesk-docs-user-guide`. Read `tools/work/writer-brief.md` first (rules, canonical paths, markup). Then read the writer's report for your page in `tools/work/reports/` and the page itself. Fix the page in place. Do not commit. Do not edit pages you were not given, except to repoint a link whose target you changed.

## What to check, in order

1. **Every `<!-- VERIFY -->` comment.** Settle it from the code on origin/develop (`git -C <repo> show origin/develop:<path>`, `git grep ... origin/develop`) or from the e2e specs. If settled, rewrite the sentence as a plain statement and delete the comment. If it needs a running instance and you cannot settle it, keep the comment but shorten it to one line that says exactly what to click and what to look for. Report the ones you kept.
2. **Version lines.** Rule: features on `origin/release/3.6` of the repo are "since 3.6"; features only on develop after the v3.6-rc1 tag are "since 3.7" (check with `git branch -r --contains <sha>` or `git log origin/release/3.6 --grep=<ticket>`). Versions go on one italic line under the heading, never in running text ("Since Superdesk 3.6 the buttons..." becomes a line under the heading or a parenthesis "(since 3.6)" at the end of the sentence when the heading covers more than that one feature).
3. **Consistency with the rest of the guide.** Use these decisions:
   - The desk dropdown in the top bar is the **Desks menu**. Not "workspace dropdown", not "desk menu".
   - The left sidebar is the **Workspace Panel**. The menu button opens the **Main menu** (the page may add "also called the hamburger menu" once).
   - The spell checker toggle sits in the status bar under the authoring top bar (not the editor header); default shortcut Alt+S, configurable with `spellchecking.shortcut`; Ctrl+Shift+Y is Tansa only.
   - Content lists, the AI Providers page and the Content lists Production API scope are "since 3.7".
   - The Unspike panel does not preselect the original desk; only the Unspike button in a read-only spiked item returns the item to its original desk and stage.
   - `PUBLISH_ASSOCIATIONS_RESEND` is dead code since 3.0; do not mention it.
   - Closed desks and the Desk Router widget predate 2.0; no version line.
   - Optional modules get the info hint at the top of their section and a "For administrators" section at the end.
   - Customer names never appear (Belga, ANSA, STT, CP, Fidelity, AAP, NTB and so on), except agency feed and parser labels in the ingest page, which the owner allowed.
4. **Duplication.** If your page repeats a procedure that another page owns (sending and publishing, spiking, locking, media, collaboration, Master Desk, Monitoring), replace it with one sentence and a link to the owning page and anchor. Anchors are GitBook slugs of the heading: lower case, spaces to hyphens, punctuation removed.
5. **Markup and style.** Every stepper, step, hint and tab block closed; steps say what to click and what happens; second person; no em-dashes; no emoji; no marketing language; no mention of authoring-react, Editor 2, Angular, React or Publisher; no links to superdesk.github.io; figures use `<figure><img ...><figcaption>` with the image under `.gitbook/assets/<page-slug>/` and a matching manifest entry in `tools/screenshots/manifests/<page-slug>.json` (image files are captured later; check the path and the manifest entry, not the file).
6. **Facts.** Spot-check five claims per page against the code: menu labels, field names, privilege labels, config keys. Fix what is wrong.

## Known cross-page issues to resolve where they fall in your pages

- `workspace-and-search/monitoring-tab.md` tells users to turn on "Enable Single Line View" in the profile; that switch sits in a hidden span on develop. Check `scripts/apps/users/` and the monitoring list; fix or remove.
- `superdesk-planning-component/planning-administration.md` says users set "Default desk for coverage types" and "Open advanced mode when adding coverages" in their profile; the profile writer found they are set from the planning UI. Settle it.
- `superdesk-planning-component/*` mentions "Add to Feature Stories" (no d). Check the real label.
- `workspace-and-search/desks-and-custom-workspaces.md` still has sections that duplicate spiking, sending from Personal Space and locking. Shorten to links.
- `content-management/creating-and-editing-content-items/*` line about the Suggestions widget listing all suggestions: it lists resolved ones only.
- `reference/keyboard-shortcuts.md` says the spell checker button is in the editor header: it is in the status bar.
- Headings containing " / " (for example "The Send to / Publish panel") get unpredictable slugs; rename such headings to avoid the slash (for example "The Send to and Publish panel") and update links that point at them.
- `workspace-and-search/highlights.md` and `content-management/packages.md` are KEEP pages but still carry Base64 placeholder images and `####` headings; if they are in your set, remove the broken images, promote headings to `##`/`###`, and add manifest entries for any image that must be recaptured.

- After the page splits, links whose text still reads "Superdesk Planning Component", "Content Configuration", "Creating and Editing Content Items", "Defining Publishing in Superdesk" or "Updates, corrections, kills and takedowns" but land on a subpage should get the subpage's title as link text. In `master-desk.md` the two assignment-related links should point at `superdesk-planning-component/assignments.md`.
- The planning overview does not link to the multilingual section in `events.md`; add one sentence with a link.

- Updates section: the kills page needs a one-sentence intro under its H1; precise targets for the no-anchor links (translating-content.md and sending page line 31 to `corrections.md`; sending page embargoed-updates sentence to `updates.md#updates-of-embargoed-stories`; templates page kill-template sentence to `README.md#kill-and-takedown-templates`; glossary "Corrections workflow" to `corrections.md#the-corrections-workflow`); sentences saying "your administrator can allow..." should link to the section README's "For administrators".

- `integrations-and-advanced-features/ai-features.md` links "Editor Sidebar" to the authoring README; the widgets section now lives at `creating-and-editing-content-items/metadata-and-fields.md#widgets`.
- `features.editorAttachments`: the authoring metadata page says it shows the Attachments widget, `asset-management.md` says it is on by default and `false` hides it. Check `scripts/apps/authoring/attachments` on develop and make both pages say the same.
- Section README pages ("In this section" lists) and the repo-root `README.md` list only section pages; add the new subpages under their section entry where the list has them for other sections (Creating and Editing Content Items, Updates, Content Configuration, Defining Publishing, Planning).

## Report

Short: page paths, VERIFY comments settled and kept (with the one-line instruction for the kept ones), version lines changed, duplication removed, facts corrected, and anything you could not resolve.
