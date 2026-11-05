#!/bin/bash
# Capture raw screenshots for one page/shot or all, against the documentation instance
# (https://sd-autodocs.test.superdesk.org, Fireq build of the superdesk repo's auto-docs branch; its
# server/scripts/autodocs/README.md explains the seed and the snapshots).
# usage: run-capture-autodocs.sh [<page-slug>[/<shot-name>]] [extra capture.mjs args]
#
# By default the instance's seeded snapshot is restored once before the first shot. That snapshot is
# dated to the day the instance was seeded. FRESH=1 restores the bare base data instead and runs the
# seeds against the instance first, so schedules, embargoes, rundowns, planning dates and locks are
# relative to today.
#
#   SNAPSHOT=autodocs           newsroom and broadcasting pages (default), browser in Europe/London
#   SNAPSHOT=autodocs-planning  Planning pages, browser in Australia/Sydney
#   AUTODOCS_URL                instance URL
#   E2E_CLIENT                  folder whose node_modules has playwright (capture.mjs --playwright-from)
#   CHROMIUM_PATH               browser binary when it is not in the Playwright cache
#
# system-messages: run `python3 seed.py --api-url <instance>/api --system-message-on` before that page
# and the plain seed right after, as on the e2e stack.
cd "$(dirname "$0")"
URL=${AUTODOCS_URL:-https://sd-autodocs.test.superdesk.org}
API="$URL/api"
SNAPSHOT=${SNAPSHOT:-autodocs}
# Playwright comes from this folder when `npm ci` was run here (package.json), otherwise from a
# superdesk-client-core e2e checkout: $E2E_CLIENT, or the sibling checkout next to the docs repo.
if [ -z "$E2E_CLIENT" ]; then
  if [ -d node_modules/playwright ]; then
    E2E_CLIENT=$(pwd)
  else
    E2E_CLIENT=$(cd ../../../superdesk-client-core/e2e/client 2>/dev/null && pwd)
  fi
fi
# A Chromium other than the one `npx playwright install chromium` put in the Playwright cache:
# $CHROMIUM_PATH, else the newest headless shell in the macOS cache, else Playwright's own lookup.
EXE=${CHROMIUM_PATH:-$(ls -d ~/Library/Caches/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell 2>/dev/null | tail -1)}
case "$SNAPSHOT" in
  autodocs-planning) TZ_NAME=Australia/Sydney ;;
  *) TZ_NAME=Europe/London ;;
esac
only=$1; shift
restore_args=(--restore --snapshot "$SNAPSHOT")
if [ -n "$FRESH" ]; then
  if [ "$SNAPSHOT" = autodocs-planning ]; then
    python3 seed_planning.py --api-url "$API" --reset || exit 1
  else
    curl -fsS -m 300 -X POST "$API/restore_record" -H 'Content-Type: application/json' \
      -d '{"name": "autodocs-base"}' > /dev/null || exit 1
    python3 seed.py --api-url "$API" && python3 seed_broadcasting.py --api-url "$API" || exit 1
  fi
  restore_args=()
fi
node capture.mjs --manifests manifests --out out/raw \
  --base-url "$URL" --api-url "$API" \
  ${E2E_CLIENT:+--playwright-from "$E2E_CLIENT"} ${EXE:+--executable-path "$EXE"} \
  --timezone "$TZ_NAME" "${restore_args[@]}" ${only:+--only $only} "$@"
