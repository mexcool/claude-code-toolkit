# Claude Code Toolkit

A collection of Claude Code plugins for enhanced development workflows.

## Available Plugins

| Plugin | Description |
|--------|-------------|
| [claude-dev-tools](./plugins/claude-dev-tools) | Context optimization and continuous learning tools |
| [cli-dev](./plugins/cli-dev) | Skills for designing and reviewing agent-friendly CLI tools |
| [obsidian-helper](./plugins/obsidian-helper) | Session notes and task tracking in Obsidian |
| [pastila](./plugins/pastila) | Encrypted pastebin sharing via [pastila.nl](https://pastila.nl/) (ClickHouse) |

## Installation

```bash
# Add the marketplace
/plugin marketplace add https://github.com/mexcool/claude-code-toolkit

# Install a plugin
/plugin install claude-dev-tools@claude-code-toolkit
```

Or use the interactive `/plugin` command to browse and install.

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
