---
name: claude-limits
description: "Check your Claude plan usage limits — session (5-hour), weekly, per-model weekly, and monthly extra-usage windows with how close each is to its ceiling. Use when asked about usage limits, rate limits, quota, or how much of the plan is left."
version: 0.1.1
---

# Claude Usage Limits

Shows the real plan-limit percentages — the same numbers the `/usage` slash
command displays — by reading the locally stored Claude Code OAuth token and
calling the usage endpoint directly.

Unlike log-based cost tools (e.g. ccusage, or the `session-cost` skill), this
reports **actual plan limits**, not token-cost estimates.

> **Presenting the result:** show the script's rendered table verbatim in a
> fenced code block — the bars and layout are the point, so don't summarize the
> numbers into prose. When capturing output for display in chat, run it
> *without* `--color` (ANSI escapes render as noise in markdown); `--color` is
> for the user's own terminal or a statusline.

## Usage

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/claude-limits/scripts/claude-limits.py          # table
uv run ${CLAUDE_PLUGIN_ROOT}/skills/claude-limits/scripts/claude-limits.py --json   # raw response
uv run ${CLAUDE_PLUGIN_ROOT}/skills/claude-limits/scripts/claude-limits.py --color  # force ANSI color (statusline / piped)
```

Example output (illustrative values):

```
Claude usage limits  ·  plan: <plan>  ·  tier: <tier>
────────────────────────────────────────────────────────────────
Window                Utilization              Resets
Session (5h)          ████████░░░░░░░░░░░░  40.0%   <day> <time> UTC (in 3.0h)
Weekly — all models   ████░░░░░░░░░░░░░░░░  22.0%   <day> <time> UTC (in 5.0d)
Weekly — Sonnet       ██░░░░░░░░░░░░░░░░░░  10.0%   <day> <time> UTC (in 5.0d)

Monthly extra-usage   ██████░░░░░░░░░░░░░░  30.0%   30.00 / 100.00 USD
```

## How it works

```
GET https://api.anthropic.com/api/oauth/usage
  Authorization: Bearer <accessToken>
  anthropic-beta: oauth-2025-04-20
```

The access token is read from (in order):
1. `$CLAUDE_CONFIG_DIR/.credentials.json`
2. `~/.claude/.credentials.json`
3. macOS Keychain item `Claude Code-credentials` (fallback)

The token's `claudeAiOauth` object must include the `user:profile` scope.

## Requirements & caveats

- **Subscription auth only** (Pro / Max / Team). Under Amazon Bedrock or a raw
  API key there are no rolling plan limits — billing is per-token, so the
  endpoint does not apply.
- The endpoint is **undocumented and beta-gated**; it may change without notice.
- If the call returns **401/403**, the token is expired or missing the
  `user:profile` scope — start any `claude` session to refresh it, then retry.
  The script intentionally does **not** refresh tokens itself, to avoid racing
  with the CLI's own token rotation.
- No credentials or tokens are written, logged, or transmitted anywhere except
  the request to the usage endpoint.
