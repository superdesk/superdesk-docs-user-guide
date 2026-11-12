#!/bin/bash
# Capture raw screenshots for one page/shot or all, against the local e2e stack.
# usage: run-capture.sh [<page-slug>[/<shot-name>]] [extra capture.mjs args]
# Assumes: client-core e2e stack on slot 2 (client :9012, api :5012) built from
# the develop worktree at Core/superdesk-client-core-docs, and the newsroom
# seeded with seed.py. Playwright 1.61 there expects Chromium 1228; the cached
# 1243 headless shell works, hence --executable-path.
cd "$(dirname "$0")"
EXE=$(ls -d ~/Library/Caches/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell | tail -1)
only=$1; shift
node capture.mjs --manifests manifests --out out/raw \
  --base-url http://localhost:9012 --api-url http://localhost:5012/api \
  --playwright-from /Users/eos87/code/SourceFabric/Superdesk/Core/superdesk-client-core-docs2/e2e/client \
  --executable-path "$EXE" --timezone Europe/London ${only:+--only $only} "$@"
