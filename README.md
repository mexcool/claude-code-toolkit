# Claude Code Toolkit

A collection of Claude Code plugins for enhanced development workflows. The agent-agnostic skills also run under **Codex** — see [Installation](#installation).

## Available Plugins

The **Codex** column marks plugins whose skills are agent-agnostic and exported by `install-codex.sh`.

| Plugin | Description | Codex |
|--------|-------------|:-----:|
| [claude-dev-tools](./plugins/claude-dev-tools) | Context optimization and continuous learning tools | — |
| [agent-sessions](./plugins/agent-sessions) | Find and resume Claude Code / Codex sessions after a terminal dies | ✓ |
| [cli-dev](./plugins/cli-dev) | Skills for designing and reviewing agent-friendly CLI tools | ✓ |
| [gist](./plugins/gist) | GitHub Gists as a lightweight pastebin via the `gh` CLI | ✓ |
| [obsidian-helper](./plugins/obsidian-helper) | Session notes and task tracking in Obsidian | — |
| [pastila](./plugins/pastila) | Encrypted pastebin sharing via [pastila.nl](https://pastila.nl/) (ClickHouse) | — |
| [prompts](./plugins/prompts) | Reusable starter prompts — `pr-review`, `ticket-kickoff` | ✓ |
| [reference-docs](./plugins/reference-docs) | Reference books/docs as on-demand skills — `inference-engineering` ([Baseten's Inference Engineering book](https://www.baseten.co/inference-engineering/)) | ✓ |
| [ponytail](https://github.com/DietrichGebert/ponytail) | Lazy senior-dev mode — YAGNI, stdlib first, no unrequested abstractions (third-party, referenced) | — |

`claude-dev-tools` is Claude-specific (usage endpoint, `/compact`, hooks, Agent Teams); `obsidian-helper` / `pastila` ship slash-commands, not skills — so neither is exported to Codex.

## Installation

### Claude Code

```bash
# Add the marketplace
/plugin marketplace add https://github.com/mexcool/claude-code-toolkit

# Install a plugin
/plugin install claude-dev-tools@claude-code-toolkit
```

Or use the interactive `/plugin` command to browse and install.

### Codex

Codex has no marketplace; it reads skills from `$CODEX_HOME/skills` (default `~/.codex/skills`). Clone this repo and symlink the agent-agnostic skills into place:

```bash
./install-codex.sh   # idempotent; re-run after pulling new skills
```

This links `agent-sessions`, `axi`, `cursor-cli-dev`, `gist`, `inference-engineering`, `pr-review`, and `ticket-kickoff` into `$CODEX_HOME/skills` (pointing back at this repo — no copies). Restart Codex to pick them up.

## Adding a Skill to an Existing Plugin

Skills are discovered automatically by directory convention — no JSON registration needed.

1. Create `plugins/<plugin-name>/skills/<skill-name>/SKILL.md`
2. Bump the `version` in `plugins/<plugin-name>/.claude-plugin/plugin.json` so the plugin system re-caches
3. Document the skill in `CLAUDE.md` under the plugin's section
4. Run `/reload-plugins` (or `/plugin` to update)

If the skill needs hooks (e.g., triggering on `PreToolUse`/`PostToolUse`), also add entries to the plugin's `hooks/hooks.json`.

## Adding New Plugins

1. Create a new directory under `plugins/`:

```
plugins/
└── new-plugin/
    ├── .claude-plugin/
    │   └── plugin.json
    ├── commands/
    ├── agents/
    ├── skills/
    └── hooks/
```

2. Add entry to `.claude-plugin/marketplace.json`:

```json
{
  "plugins": [
    {
      "name": "new-plugin",
      "source": "./plugins/new-plugin",
      "description": "Description here"
    }
  ]
}
```

## Credits

- Skills in `claude-dev-tools` are adapted from [everything-claude-code](https://github.com/affaan-m/everything-claude-code) by [@affaanmustafa](https://x.com/affaanmustafa), licensed under MIT.
- `cli-dev:axi` is from [kunchenguid/axi](https://github.com/kunchenguid/axi) by Kun Cheng, licensed under MIT.
- `cli-dev:cursor-cli-dev` is from [cursor/plugins](https://github.com/cursor/plugins/blob/main/cli-for-agent/skills/cli-for-agents/SKILL.md) by Cursor.
- `obsidian-helper` is inspired by [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) by Steph Ango (Obsidian).
- `ponytail` is [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) by Dietrich Gebert, licensed under MIT. This marketplace references it via a pinned `github` source (v4.5.0) — no code is copied into this repo.
