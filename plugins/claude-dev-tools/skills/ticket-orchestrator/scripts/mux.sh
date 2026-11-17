#!/usr/bin/env bash
# Every pane and agent call the lead makes, on herdr (HERDR_ENV=1) or Rex (REX_SESSION set).
# herdr wins when both are set: a herdr started from a Rex terminal inherits REX_SESSION, and the
# pane belongs to herdr. Agent state comes from herdr's screen detection, or under Rex from the
# status the agent reports itself (OSC 7501). After `start`, the name works wherever <agent> is asked.
set -o pipefail

usage() {
  cat >&2 <<'EOF'
usage: mux.sh <command> [args]
  columns <cwd>                            two more equal columns right of this pane; prints their ids
  split-below <pane> <cwd>                 a pane below <pane>; prints its id
  start <pane> <name> claude|codex <cmd>   type <cmd> into the pane's shell, wait until the agent is ready, name it
  name-self <name> <tab-label>             name this pane and its tab
  send <agent> <text>                      submit <text> without waiting for a turn (for /rename)
  prompt <agent> <text> [timeout-s]        submit <text> and wait until the turn ends; prints the agent's state
  wait <agent> working|settled [timeout-s]
  read <agent>                             the agent's recent screen
  close <pane>
EOF
  exit 64
}
(($# >= 2)) || usage

herdr_mux() {
  case $1 in
    columns)
      impl=$(herdr pane split "$HERDR_PANE_ID" --direction right --cwd "$2" --no-focus | jq -er .result.pane.pane_id) || exit
      rev=$(herdr pane split "$impl" --direction right --cwd "$2" --no-focus | jq -er .result.pane.pane_id) || exit
      herdr pane resize --direction left --amount 0.17 --pane "$impl" >/dev/null || exit # 1/2,1/4,1/4 → thirds
      echo "$impl $rev" ;;
    split-below) herdr pane split "$2" --direction down --cwd "$3" --no-focus | jq -er .result.pane.pane_id ;;
    start)
      herdr pane run "$2" "$5" >/dev/null || exit
      # herdr's agent detection, not a screen regex: a shell prompt can show the same glyph as an agent.
      deadline=$((SECONDS + 60))
      until json=$(herdr agent get "$2" 2>/dev/null) &&
        [[ $json == *"\"agent\":\"$4\""* && $json =~ \"agent_status\":\"(idle|done)\" ]]; do
        ((SECONDS < deadline)) || { echo "mux: no ready $4 agent in $2 after 60s" >&2; exit 1; }
        sleep 1
      done
      herdr agent rename "$2" "$3" >/dev/null && herdr pane rename "$2" "$3" >/dev/null ;;
    name-self) herdr agent rename "$HERDR_PANE_ID" "$2" >/dev/null && herdr tab rename "$HERDR_TAB_ID" "$3" >/dev/null ;;
    send) herdr agent prompt "$2" "$3" ;;
    prompt) herdr agent prompt "$2" "$3" --wait --timeout "$((${4:-3600} * 1000))" ;;
    wait)
      if [[ $3 == working ]]; then herdr agent wait "$2" --until working --timeout "$((${4:-3600} * 1000))"
      else herdr agent wait "$2" --timeout "$((${4:-3600} * 1000))"; fi ;;
    read) herdr agent read "$2" ;;
    close) herdr pane close "$2" ;;
    *) usage ;;
  esac
}

S=${REX_SESSION:-}
agent() { # <agent> <jq args>: agent.lua against the agent's pane, its arguments built by jq
  local b=$1; shift
  jq -nc "$@" | rex do -s "$S" -b "$b" "${BASH_SOURCE[0]%/*}/agent.lua" --args -
}

rex_mux() {
  case $1 in
    columns)
      impl=$(rex split -s "$S" -b "$REX_BLOCK" --split=right --ratio 67 -c "$2" --focus=false --json | jq -er '.block_ids[0]') || exit
      rev=$(rex split -s "$S" -b "$impl" --split=right --ratio 50 -c "$2" --focus=false --json | jq -er '.block_ids[0]') || exit
      echo "$impl $rev" ;;
    split-below) rex split -s "$S" -b "$2" --split=below -c "$3" --focus=false --json | jq -er '.block_ids[0]' ;;
    start)
      app=$4; [[ $app == claude ]] && app=claude-code
      rex block rename -s "$S" "$2" "$3" >/dev/null || exit
      rex send -s "$S" -b "$3" "$5" && rex send-key -s "$S" -b "$3" enter || exit
      agent "$3" --arg app "$app" '{ready: $app, timeout: 60}' >/dev/null ;;
    name-self)
      window=$(rex block inspect -s "$S" "$REX_BLOCK" --json | jq -er .block.window_id) || exit
      rex block rename -s "$S" "$REX_BLOCK" "$2" >/dev/null && rex window rename -s "$S" "$window" "$3" >/dev/null ;;
    send) agent "$2" --arg t "$3" '{text: $t, timeout: 0}' ;;
    prompt) agent "$2" --arg t "$3" --argjson n "${4:-3600}" '{text: $t, timeout: $n}' ;;
    wait) agent "$2" --arg w "$3" --argjson n "${4:-3600}" '{wait: $w, timeout: $n}' ;;
    read) rex capture -s "$S" -b "$2" --trim --unwrap | tail -n 120 ;;
    close) rex block close -s "$S" "$2" ;;
    *) usage ;;
  esac
}

if [[ ${HERDR_ENV:-} == 1 ]]; then herdr_mux "$@"
elif [[ -n $S ]]; then rex_mux "$@"
else echo "mux: run inside herdr (HERDR_ENV=1) or Rex (REX_SESSION)" >&2; exit 1; fi
