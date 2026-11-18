#!/usr/bin/env bash
# wait-until.sh <HH:MM>
# Waits until that UTC time (today, or tomorrow when it has passed), prints it, and exits.
#
# Exists already: a scheduler or a wakeup tool of the harness, when there is one. Use that in its place.
set -euo pipefail
if [[ $# -ne 1 || $1 == -h || $1 == --help ]]; then
  sed -n '2,/^set /p' "$0" | sed '$d;s/^# \{0,1\}//' >&2
  exit 64
fi
target=$(date -u -d "today $1" +%s)
((target > $(date -u +%s))) || target=$(date -u -d "tomorrow $1" +%s)
while (($(date -u +%s) < target)); do
  sleep 30
done
echo "reached $1 UTC at $(date -u +%H:%M:%SZ)"
