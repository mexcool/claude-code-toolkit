#!/usr/bin/env bash
# Wait until herdr detects <kind> (claude, codex, ...) in <pane> and it is ready for input.
# Uses herdr's agent detection, not a raw screen regex: a shell prompt can show the same glyph as an agent.
# Usage: wait-agent.sh <pane-id> <kind> [timeout-seconds, default 60]
pane=$1 kind=$2 deadline=$((SECONDS + ${3:-60}))
while ((SECONDS < deadline)); do
  json=$(herdr agent get "$pane" 2>/dev/null)
  if [[ $json == *"\"agent\":\"$kind\""* && $json =~ \"agent_status\":\"(idle|done)\" ]]; then
    exit 0
  fi
  sleep 1
done
echo "wait-agent: no ready $kind agent in $pane after ${3:-60}s" >&2
exit 1
