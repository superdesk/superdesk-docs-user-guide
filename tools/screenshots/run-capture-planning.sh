#!/bin/bash
# Capture raw screenshots for the planning pages (or any page/shot) against the
# superdesk-planning e2e stack.
# usage: run-capture-planning.sh [<page-slug>[/<shot-name>]] [extra capture.mjs args]
# Assumes: superdesk-planning e2e stack on slot 1 (client :9021, api :5021)
# built from the develop worktree at Core/superdesk-planning-docs, and the data
# seeded with `seed_planning.py --reset`. Never pass --restore here: that stack
# has no restore_record endpoint. Playwright 1.62 there expects Chromium 1234;
# the cached 1243 headless shell works, hence --executable-path.
cd "$(dirname "$0")"
EXE=$(ls -d ~/Library/Caches/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell | tail -1)
only=$1; shift
# Release item and Featured Stories locks and delete editor autosaves left by earlier runs (an editor that
# a shot opened stays locked for that session); the seed skips everything that already exists.
[ -n "$NO_SEED" ] || python3 seed_planning.py --api-url http://localhost:5021/api | grep -E 'unlock|delete|error' || true
node capture.mjs --manifests manifests --out out/raw \
  --base-url http://localhost:9021 --api-url http://localhost:5021/api \
  --playwright-from /Users/eos87/code/SourceFabric/Superdesk/Core/superdesk-planning-docs/e2e \
  --executable-path "$EXE" --timezone Australia/Sydney ${only:+--only $only} "$@"
