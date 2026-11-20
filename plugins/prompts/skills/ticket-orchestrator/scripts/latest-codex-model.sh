#!/usr/bin/env bash
# Print the newest listed release of a Codex model family.
set -euo pipefail

if [[ $# != 1 || ! $1 =~ ^(astra|sol)$ ]]; then
  echo "usage: latest-codex-model.sh astra|sol" >&2
  exit 64
fi

codex debug models | jq -er --arg family "$1" '
  [.models[] | select(.visibility == "list") | .slug
   | select(test("^gpt-[0-9]+(\\.[0-9]+)*-" + $family + "$"))]
  | max_by(split("-")[1] | split(".") | map(tonumber))
    // error("no listed Codex release for " + $family)
'
