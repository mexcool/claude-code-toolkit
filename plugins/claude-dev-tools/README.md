# claude-dev-tools

Plan usage limits and follow-up checks for Claude Code.

The ticket orchestrator moved to the `prompts` plugin. Install `prompts@claude-code-toolkit` for `/prompts:ticket-orchestrator`. [Orchestrator guide](../../docs/ticket-orchestrator.html)

## Skills

### claude-limits

Shows your real Claude plan usage limits — session (5-hour), weekly, per-model weekly, and monthly extra-usage windows — by reading the locally stored OAuth token and calling the usage endpoint. Unlike log-based cost tools, this reports actual plan-limit percentages, not estimates.

```bash
uv run skills/claude-limits/scripts/claude-limits.py          # table
uv run skills/claude-limits/scripts/claude-limits.py --json   # raw response
```

Subscription auth only (Pro/Max/Team); not applicable under Bedrock or a raw API key.

### follow-up-check

Schedules a check on shipped work that cannot be verified yet. A Linear comment posted now points at a gist with the check plan, scripts and baselines, and a native Linear reminder pings the user on the due date.

```bash
uv run skills/follow-up-check/scripts/follow-up.py due --days 14  # next weekday morning, UTC; warns near transcript expiry
uv run skills/follow-up-check/scripts/follow-up.py session        # id, start cwd, resume command
```

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

