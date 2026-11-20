#!/usr/bin/env bash
# wait-runs.sh <owner/repo> <run-id>...
# Waits (up to 40 minutes) until each CI run is completed, then prints one line for each:
# run id, status, conclusion, head sha.
#
# Exists already: `gh run watch <id>` for one run. Use this one for several runs at once.
set -euo pipefail
if [[ $# -lt 2 || $1 == -h || $1 == --help ]]; then
  sed -n '2,/^set /p' "$0" | sed '$d;s/^# \{0,1\}//' >&2
  exit 64
fi
repo=$1; shift
for _ in $(seq 1 80); do
  pending=0
  for id in "$@"; do
    [[ $(gh run view "$id" --repo "$repo" --json status --jq .status) == completed ]] || pending=1
  done
  ((pending)) || break
  sleep 30
done
for id in "$@"; do
  gh run view "$id" --repo "$repo" --json databaseId,status,conclusion,headSha \
    --jq '[.databaseId, .status, (.conclusion // "-"), .headSha[0:9]] | @tsv'
done
