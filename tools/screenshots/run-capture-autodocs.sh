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
#   E2E_CLIENT                  folder whose node_modules has playwright (capture.mjs --playwright-from);
#                               SUPERDESK_E2E_CLIENT is accepted as well
#   MANIFESTS, OUT              manifest folder and raw output folder (default manifests, out/raw), for a
#                               scratch manifest outside the repo
#   CHROMIUM_PATH               browser binary when it is not in the Playwright cache
#
# system-messages: the restore would undo the active message, so for that page the script restores
# first, turns the seeded message on (seed.py --system-message-on), captures without a restore and
# runs the plain seed afterwards so the toast does not stay on the instance.
cd "$(dirname "$0")"
URL=${AUTODOCS_URL:-https://sd-autodocs.test.superdesk.org}
API="$URL/api"
SNAPSHOT=${SNAPSHOT:-autodocs}
# Playwright comes from this folder when `npm ci` was run here (package.json), otherwise from a
# superdesk-client-core e2e checkout: $E2E_CLIENT, or the sibling checkout next to the docs repo.
E2E_CLIENT=${E2E_CLIENT:-$SUPERDESK_E2E_CLIENT}
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
system_messages=
case "$only" in system-messages*) system_messages=1 ;; esac
if [ -n "$system_messages" ]; then
  if [ -n "${restore_args[*]}" ]; then
    curl -fsS -m 300 -X POST "$API/restore_record" -H 'Content-Type: application/json' \
      -d "{\"name\": \"$SNAPSHOT\"}" > /dev/null || exit 1
  fi
  python3 seed.py --api-url "$API" --system-message-on || exit 1
  restore_args=()
fi
node capture.mjs --manifests "${MANIFESTS:-manifests}" --out "${OUT:-out/raw}" \
  --base-url "$URL" --api-url "$API" \
  ${E2E_CLIENT:+--playwright-from "$E2E_CLIENT"} ${EXE:+--executable-path "$EXE"} \
  --timezone "$TZ_NAME" "${restore_args[@]}" ${only:+--only $only} "$@"
status=$?
if [ -n "$system_messages" ]; then
  python3 seed.py --api-url "$API" > /dev/null || echo "warning: could not deactivate the system message" >&2
fi
exit $status
