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
- Environment: needs Node 20 or newer, Python 3 with Pillow (`pip install pillow`), `gh` logged in with write access to the docs repo, and `npm ci && npx playwright install --with-deps chromium` in `tools/screenshots` (the skill runs it when missing; `--with-deps` needs root for the apt packages, so put them in the environment's setup script if the sandbox has no root). Outbound access to `https://sd-autodocs.test.superdesk.org`.

## Rollout

1. superdesk-client-core first, watch the first three runs and fix the skill from what they get wrong.
2. Then superdesk-planning and superdesk-core (same prompt, repo name changed), last superdesk-analytics.
3. The docs instance follows the `auto-docs` branch of `superdesk/superdesk`, which pins client-core in `client/package-lock.json` and the server packages in `server/requirements.txt`. Until something bumps those pins after a merge, a run right after a merge finds the instance behind and leaves its shots pending in a draft PR. Nothing picks those up on its own yet: someone re-runs `/docs-update` for the same PR once the instance has the change, and the skill continues the existing branch. Automating both is the follow-up: a workflow on `superdesk/superdesk` that merges develop into `auto-docs` after each dependabot bump, and a weekly sweep over open `docs-update/*` drafts.
