# Docs update routine: prompt and setup

The cloud routine that keeps the user guide in step with merged product PRs (SDESK-8055). One routine per product repo, all pointing at this docs repo. The agent runs the `docs-update` skill in `.claude/skills/docs-update/SKILL.md`; this file only holds what goes into the routine itself.

## Prompt

Paste as the routine's message. The GitHub trigger appends the pull request event as data; when running by hand replace the first line with the PR reference.

```
A pull request was merged in superdesk/superdesk-client-core. The event data is below this message.

You are in a checkout of superdesk/superdesk-docs-user-guide on main. Run the docs-update skill (.claude/skills/docs-update/SKILL.md) for that pull request: decide whether it is user-facing, update the affected pages, recapture the screenshots it changed on the docs instance, and open a draft-or-ready docs PR against main for a human to review. If the PR is not user-facing, do not create a branch or PR; just report why.

Rules that are not negotiable: edit only the pages the change affects, ground every label and menu path in the merged code, never push to main, never commit tools/screenshots/out, no em-dashes and no emoji anywhere. End with the short report the skill asks for.
```

For a manual run (`claude` on a laptop, in this repo): `/docs-update https://github.com/superdesk/superdesk-client-core/pull/<number>`.

## Routine settings

- Repository: `superdesk/superdesk-docs-user-guide`, branch `main`.
- Trigger: GitHub, repository `superdesk/superdesk-client-core`, event pull request closed with merged = true, base branch `develop`. Needs the Claude GitHub App on that repository (installed 3 Nov 2026) and GitHub connected to the Claude account that owns the routine.
- Model: Opus. The judgement in step 1 and the page edits are the expensive part, not the tool calls.
- Tools: Bash, Read, Write, Edit, Glob, Grep. No connectors needed.
- Environment: the cloud environment below. Needs outbound access to `https://sd-autodocs.test.superdesk.org`.

## Cloud environment (claude.ai/code, environment settings)

- Network access: Custom, with "Also include default list of common package managers" checked (GitHub, npm, PyPI, apt), plus one line: `sd-autodocs.test.superdesk.org`.
- Environment variables (`.env` format):
  - `CHROMIUM_PATH=/usr/bin/google-chrome` (Chrome for Testing is preinstalled in the image, so Playwright downloads nothing)
  - `AUTODOCS_URL=https://sd-autodocs.test.superdesk.org`
  - `BASH_DEFAULT_TIMEOUT_MS=600000` (a capture run can take longer than the two-minute default)
- Setup script (runs as root on a fresh image, before the environment variables exist and apparently outside the repo checkout, so it must not rely on either and must exit 0 or the session is aborted). The skill runs `npm ci` itself, so the script only preinstalls Pillow for the styling scripts:

  ```sh
  pip install pillow || true
  exit 0
  ```

- The image has Node 22 first on PATH (20 and 21 under `/opt`), Python 3 with pip, `git` and `gh`. The GitHub proxy allows REST (`gh api`) and rejects GraphQL, so the skill never uses `gh pr`.
- The repo's `.claude/skills/docs-update` loads in the session because the docs repo is the first and only full checkout of the task. The other sources (client-core, superdesk, superdesk-core) are sparse checkouts of a single file each; they exist only so the GitHub proxy lets `gh api` read those repositories.

## Rollout

1. superdesk-client-core first, watch the first three runs and fix the skill from what they get wrong.
2. Then superdesk-planning and superdesk-core (same prompt, repo name changed), last superdesk-analytics.
3. The docs instance follows the `auto-docs` branch of `superdesk/superdesk`, which pins client-core in `client/package-lock.json` and the server packages in `server/requirements.txt`. Until something bumps those pins after a merge, a run right after a merge finds the instance behind and leaves its shots pending in a draft PR. Nothing picks those up on its own yet: someone re-runs `/docs-update` for the same PR once the instance has the change, and the skill continues the existing branch. Automating both is the follow-up: a workflow on `superdesk/superdesk` that merges develop into `auto-docs` after each dependabot bump, and a weekly sweep over open `docs-update/*` drafts.
