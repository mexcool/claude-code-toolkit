#!/usr/bin/env bash
# Install this toolkit's agent-agnostic skills into Codex.
#
# Claude consumes this repo as a plugin marketplace (`/plugin marketplace add …`).
# Codex has no marketplace, but reads skills from $CODEX_HOME/skills — so this
# script symlinks the agent-agnostic skills there. The skills stay where they
# live (plugins/<plugin>/skills/<skill>/); Codex just gets symlinks. One source,
# no copies, idempotent, safe to re-run.
#
# Only agent-agnostic plugins are exported. Skipped on purpose:
#   claude-dev-tools          every skill is Claude-specific (OAuth usage
#                             endpoint, /compact, Claude hooks, Agent Teams)
#   obsidian-helper, pastila  slash-commands, not skills (Claude command format)
# To export a new plugin's skills, add it to AGENT_AGNOSTIC_PLUGINS below.
#
# Usage: ./install-codex.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_SKILLS="${CODEX_HOME:-$HOME/.codex}/skills"

AGENT_AGNOSTIC_PLUGINS=(agent-sessions cli-dev gist prompts)

mkdir -p "$CODEX_SKILLS"
echo "Installing agent-agnostic skills into $CODEX_SKILLS"

linked=0 skipped=0
for plugin in "${AGENT_AGNOSTIC_PLUGINS[@]}"; do
    for src in "$REPO_DIR/plugins/$plugin/skills"/*/; do
        [ -d "$src" ] || continue          # no skills dir / empty glob
        src="${src%/}"
        name="$(basename "$src")"
        dest="$CODEX_SKILLS/$name"

        if [ -L "$dest" ]; then
            target="$(readlink "$dest")"
            if [ "$target" = "$src" ]; then
                echo "  = $name (already linked)"
            elif [[ "$target" == "$REPO_DIR/"* ]]; then
                ln -sfn "$src" "$dest"; echo "  ~ $name (repointed)"; linked=$((linked + 1))
            else
                echo "  ! $name — skipped (links elsewhere: $target)"; skipped=$((skipped + 1))
            fi
        elif [ -e "$dest" ]; then
            echo "  ! $name — skipped (a real file/dir is already there)"; skipped=$((skipped + 1))
        else
            ln -s "$src" "$dest"; echo "  + $name"; linked=$((linked + 1))
        fi
    done
done

echo "Done: $linked linked, $skipped skipped. Restart Codex to pick up new skills."
