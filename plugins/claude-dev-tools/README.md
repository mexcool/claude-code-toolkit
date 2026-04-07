# claude-dev-tools

Context optimization and continuous learning tools for Claude Code development.

## Skills

### strategic-compact

Suggests manual `/compact` at strategic points in your workflow rather than relying on arbitrary auto-compaction.

- Tracks tool call counts during sessions
- Suggests compaction at logical task boundaries
- Configurable threshold via `COMPACT_THRESHOLD` env var

### continuous-learning-v2

Instinct-based learning system that observes your sessions and creates atomic "instincts" - small learned behaviors with confidence scoring.

**Commands:**
- `/instinct-status` - Show all learned instincts with confidence levels
- `/evolve` - Cluster related instincts into skills/commands/agents
- `/instinct-export` - Export instincts for sharing
- `/instinct-import <file>` - Import instincts from others

## Installation

Add to your Claude Code settings:

```bash
claude --plugin-dir /path/to/claude-code-plugins/plugins/claude-dev-tools
```

Or add to `~/.claude/settings.json`:

```json
{
  "plugins": [
    "/path/to/claude-code-plugins/plugins/claude-dev-tools"
  ]
}
```

## Setup

Initialize the continuous learning directory structure:

```bash
mkdir -p ~/.claude/homunculus/{instincts/{personal,inherited},evolved/{agents,skills,commands}}
touch ~/.claude/homunculus/observations.jsonl
```

## Hooks

This plugin automatically registers hooks for:
- **PreToolUse (Edit|Write)**: Strategic compact suggestions
- **PreToolUse/PostToolUse (*)**: Session observation for learning

## Credits

The `strategic-compact` and `continuous-learning-v2` skills are adapted from [everything-claude-code](https://github.com/affaan-m/everything-claude-code) by [@affaanmustafa](https://x.com/affaanmustafa), licensed under MIT.
