#!/bin/bash
# Continuous Learning v2 - Observation Hook
#
# Captures tool use events for pattern analysis using jq for reliable JSON parsing.
# Claude Code passes hook data via stdin as JSON.

CONFIG_DIR="${HOME}/.claude/homunculus"
OBSERVATIONS_FILE="${CONFIG_DIR}/observations.jsonl"
MAX_FILE_SIZE_MB=10

# Ensure directory exists
mkdir -p "$CONFIG_DIR"

# Skip if disabled
[ -f "$CONFIG_DIR/disabled" ] && exit 0

# Read JSON from stdin
INPUT_JSON=$(cat)
[ -z "$INPUT_JSON" ] && exit 0

# Check if jq is available
if ! command -v jq &> /dev/null; then
  echo "jq not found, skipping observation" >&2
  exit 0
fi

# Archive if file too large
if [ -f "$OBSERVATIONS_FILE" ]; then
  file_size_mb=$(du -m "$OBSERVATIONS_FILE" 2>/dev/null | cut -f1)
  if [ "${file_size_mb:-0}" -ge "$MAX_FILE_SIZE_MB" ]; then
    archive_dir="${CONFIG_DIR}/observations.archive"
    mkdir -p "$archive_dir"
    mv "$OBSERVATIONS_FILE" "$archive_dir/observations-$(date +%Y%m%d-%H%M%S).jsonl"
  fi
fi

# Parse and write observation using jq
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "$INPUT_JSON" | jq -c --arg ts "$timestamp" '{
  timestamp: $ts,
  event: (if (.hook_event_name // "") | contains("Pre") then "tool_start" else "tool_complete" end),
  tool: (.tool_name // "unknown"),
  session: (.session_id // "unknown"),
  input: (if (.hook_event_name // "") | contains("Pre") then (.tool_input | tostring)[0:2000] else null end),
  output: (if (.hook_event_name // "") | contains("Post") then (.tool_response | tostring)[0:2000] else null end)
} | with_entries(select(.value != null))' >> "$OBSERVATIONS_FILE" 2>/dev/null || true

# Signal observer if running
OBSERVER_PID_FILE="${CONFIG_DIR}/.observer.pid"
if [ -f "$OBSERVER_PID_FILE" ]; then
  observer_pid=$(cat "$OBSERVER_PID_FILE")
  kill -0 "$observer_pid" 2>/dev/null && kill -USR1 "$observer_pid" 2>/dev/null || true
fi

exit 0
