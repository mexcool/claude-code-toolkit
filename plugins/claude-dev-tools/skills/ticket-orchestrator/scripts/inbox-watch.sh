#!/usr/bin/env bash
# inbox-watch.sh <file> [state-file]
# Blocks until <file> has lines that the last call did not print, prints them, and stores the
# number of lines seen in the state file (default <file>.seen), so the caller passes no line
# count. Polls every 30 s. Exits 0 after printing; exits 1 after 12 hours with no new line.
#
# Exists already: under the herdr app a child reports with `hc send` and the parent waits with
# `hc wait --children`. Use that when each lead is a child. The file stays the durable record.
set -euo pipefail
if [[ $# -lt 1 || $1 == -h || $1 == --help ]]; then
  sed -n '2,/^set /p' "$0" | sed '$d;s/^# \{0,1\}//' >&2
  exit 64
fi
file=$1
state=${2:-$file.seen}
seen=$(cat "$state" 2>/dev/null || echo 0)
touch "$file"
for _ in $(seq 1 1440); do
  now=$(wc -l < "$file")
  if ((now > seen)); then
    tail -n "+$((seen + 1))" "$file"
    echo "$now" > "$state"
    exit 0
  fi
  sleep 30
done
echo "no new line in 12 hours (still $seen lines)" >&2
exit 1
