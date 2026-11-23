#!/usr/bin/env bash
# Every pane and agent call the lead makes, on herdr (HERDR_ENV=1), Rex (REX_SESSION set) or
# herdr-core, the herdr app's terminal engine (HC_TERMINAL_ID set).
# herdr wins when both are set: a herdr started from a Rex terminal inherits REX_SESSION, and the
# pane belongs to herdr. Agent state comes from herdr's screen detection, or under Rex and herdr-core
# from the status the agent reports itself (OSC 7501). After `start`, the name works wherever <agent> is asked.
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

# herdr-core (hc): terminal addresses (t11) stand in for pane ids. hc can't rename a terminal, so the
# worker's name is a label, mux.name=<name>, and every <agent> resolves through it.
hc_addr() {
  local address
  if [[ $1 =~ ^([a-z0-9_-]+/)?t[0-9a-z]+$ ]]; then
    # A label such as "test" also looks like a terminal id. Check the actual address.
    address=$(hc get "$1" --json 2>/dev/null | jq -r .address)
    if [[ $address == "$1" || $address == "${1##*/}" ]]; then echo "$1"; return; fi
  fi
  hc ls --json --label "mux.name=$1" | jq -er '.terminals[0].address' || { echo "mux: no terminal named $1" >&2; return 1; }
}

hc_shell() { # <cwd>: a plain shell next to the lead, in the lead's app tab when the lead has one
  local labels=() l
  while read -r l; do labels+=(--label "$l"); done < <(hc get "$HC_TERMINAL_ID" --json |
    jq -r '(.labels // {}) | to_entries[] | select(.key == "herdr.space" or .key == "herdr.tab") | "\(.key)=\(.value)"')
  hc run --bg --json --cwd "$1" --outlive-parent --no-notify "${labels[@]}" | jq -er .address
}

hc_settled() { # <terminal> <deadline> <last state>
  local terminal=$1 deadline=$2 state=$3 remaining
  # A message to the lead can end hc's wait while the worker is still working.
  while [[ $state == working ]]; do
    remaining=$((deadline - SECONDS))
    ((remaining > 0)) || break
    state=$(hc wait "$terminal" --timeout "$remaining" --json | jq -er .status) || return
  done
  echo "$state"
}

hc_mux() {
  local t state deadline
  case $1 in
    columns)
      impl=$(hc_shell "$2") || exit
      rev=$(hc_shell "$2") || exit
      echo "$impl $rev" ;;
    split-below) hc_shell "$3" ;;
    start)
      app=$4; [[ $app == claude ]] && app=claude-code
      hc label "$2" "mux.name=$3" >/dev/null || exit
      hc send "$2" "$5" >/dev/null || exit
      deadline=$((SECONDS + 60))
      until json=$(hc get "$2" --json 2>/dev/null) &&
        jq -e --arg a "$app" '.status.app == $a and (.status.state | IN("idle", "done"))' <<<"$json" >/dev/null; do
        ((SECONDS < deadline)) || { echo "mux: no ready $4 agent in $2 after 60s" >&2; exit 1; }
        sleep 1
      done ;;
    # hc can't rename an app tab, and herdr-app runs only on the machine with the window. The
    # tab-names mod in that window renames the tab from the tab.name label (herdr-extensions).
    name-self) hc label "$HC_TERMINAL_ID" "mux.name=$2" "tab.name=$3" >/dev/null ;;
    # With a sender terminal, hc prefixes the text, so /rename becomes a prompt.
    send) t=$(hc_addr "$2") && env -u HC_TERMINAL_ID hc send "$t" "$3" ;;
    prompt) # a send to a blocked terminal fails without --force: the wanted refusal
      t=$(hc_addr "$2") || exit
      deadline=$((SECONDS + ${4:-3600}))
      state=$(hc send --wait --timeout "${4:-3600}" --json "$t" "$3" | jq -er .wait.status) || exit
      hc_settled "$t" "$deadline" "$state" ;;
    wait)
      t=$(hc_addr "$2") || exit
      if [[ $3 == working ]]; then
        # .turn changes when a turn runs, so a turn that starts and ends between two polls still counts
        deadline=$((SECONDS + ${4:-3600}))
        turn=$(hc get "$t" --json | jq -er .turn) || exit
        until json=$(hc get "$t" --json) && jq -e --argjson n "$turn" '.status.state == "working" or .turn != $n' <<<"$json" >/dev/null; do
          ((SECONDS < deadline)) || { echo "mux: $2 not working after ${4:-3600}s" >&2; exit 1; }
          sleep 1
        done
        echo working
      else
        deadline=$((SECONDS + ${4:-3600}))
        state=$(hc wait "$t" --timeout "${4:-3600}" --json | jq -er .status) || exit
        hc_settled "$t" "$deadline" "$state"
      fi ;;
    read) t=$(hc_addr "$2") && hc read "$t" --lines 120 ;;
    close) t=$(hc_addr "$2") && hc kill "$t" ;;
    *) usage ;;
  esac
}

if [[ ${HERDR_ENV:-} == 1 ]]; then herdr_mux "$@"
elif [[ -n $S ]]; then rex_mux "$@"
elif [[ -n ${HC_TERMINAL_ID:-} ]]; then hc_mux "$@"
else echo "mux: run inside herdr (HERDR_ENV=1), Rex (REX_SESSION) or the herdr app (HC_TERMINAL_ID)" >&2; exit 1; fi
