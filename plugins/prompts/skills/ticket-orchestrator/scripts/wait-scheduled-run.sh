#!/usr/bin/env bash
# wait-scheduled-run.sh <owner/repo> <workflow> <after-iso-time>
# Waits (up to 20 hours) for a scheduled run of <workflow> (file name or id) that was created after
# <after-iso-time> (UTC, like 2025-01-31T04:00:00Z) and is completed. Prints its id, creation time,
# conclusion and head sha. Exits 1 when none appears.
#
# Exists already: nothing equal in `gh`. `gh run watch` needs a run id, and a scheduled run has none yet.
set -euo pipefail
if [[ $# -ne 3 || $1 == -h || $1 == --help ]]; then
  sed -n '2,/^set /p' "$0" | sed '$d;s/^# \{0,1\}//' >&2
  exit 64
fi
repo=$1 workflow=$2 after=$3
for _ in $(seq 1 240); do
  line=$(gh run list --repo "$repo" --workflow "$workflow" --event schedule --limit 5 \
    --json databaseId,createdAt,status,conclusion,headSha \
    | jq -r --arg after "$after" '[.[] | select(.createdAt > $after and .status == "completed")][0]
        | select(. != null) | [.databaseId, .createdAt, .conclusion, .headSha[0:9]] | @tsv')
  if [[ -n $line ]]; then
    echo "$line"
    exit 0
  fi
  sleep 300
done
echo "no completed scheduled run after $after in 20 hours" >&2
exit 1
