# claude-dev-tools

Plan usage limits, follow-up checks and ticket orchestration for Claude Code.

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

### ticket-orchestrator

Runs one ticket with two workers in herdr panes: a Claude implementer (kickoff, code, PR) and a Codex reviewer (kickoff review, PR review). The lead only relays handoff files, sorts findings into must-fix, should-fix, user call and drop, and runs the steps that need the user. The lead sends with a background `herdr agent prompt --wait`, so herdr's screen-detected agent state wakes it when a worker's turn ends; nobody polls. The lead keys on the handoff file, not on the state label. Set `ORCH_CLAUDE_CMD` / `ORCH_CODEX_CMD` to use your own launch commands. The lead runs on Fable, the implementer on Opus, the reviewer on Sol and the blind reviewer on Sonnet, each the latest release unless you name another model. The two reviewers are on different models on purpose: two reviewers on one model raise the same findings.

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

