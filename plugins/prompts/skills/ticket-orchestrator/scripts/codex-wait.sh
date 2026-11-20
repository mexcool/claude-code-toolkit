#!/usr/bin/env bash
# Run one blocking wait, save its output and wake the originating Codex thread.
set -eu

if [[ $# -lt 2 || $1 != /* ]]; then
  echo "usage: codex-wait.sh <absolute-result-file> <command> [args...]" >&2
  exit 64
fi
: "${CODEX_THREAD_ID:?run this from the Codex lead or parent}"
codex queue --help >/dev/null
result=$1
shift
pending=$(mktemp "${result}.XXXXXX")
trap 'rm -f "$pending"' EXIT

status=0
"$@" >"$pending" 2>&1 || status=$?
printf '\nWait exit status: %d\n' "$status" >>"$pending"
mv "$pending" "$result"
codex queue --thread "$CODEX_THREAD_ID" --message "Orchestrator wait finished (exit $status). Read $result and check the expected handoff."
exit "$status"
