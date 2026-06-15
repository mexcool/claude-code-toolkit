# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Public Repository

This is a **public open-source repo**. All content is visible to anyone. Follow these practices:
- Never commit secrets, API keys, tokens, or credentials
- Use generic examples (e.g., `PROJ-123`) — no internal project names, team prefixes, or real ticket IDs
- No internal URLs, Slack channels, employee names, or company-specific references
- Review diffs before committing for accidental leaks

## Project Overview

This is a Claude Code plugin marketplace containing reusable plugins for enhanced development workflows. Plugins provide skills, hooks, commands, and agents that extend Claude Code's functionality.

## Repository Structure

```
.claude-plugin/marketplace.json    # Marketplace manifest listing available plugins
plugins/
└── <plugin-name>/
    ├── .claude-plugin/plugin.json # Plugin manifest (name, version, hooks reference)
    ├── hooks/hooks.json           # Hook definitions for plugin events
    ├── skills/                    # Skill definitions (SKILL.md files)
    ├── commands/                  # Command definitions (.md files)
    └── agents/                    # Agent definitions (.md files)
```

## Current Plugins

### claude-dev-tools

Context optimization, continuous learning, and agent orchestration tools:

- **strategic-compact**: Suggests manual `/compact` at logical task boundaries instead of arbitrary auto-compaction. Triggers on Edit/Write tool use after configurable threshold (default: 50 tool calls).

- **continuous-learning-v2**: Instinct-based learning system that observes sessions via PreToolUse/PostToolUse hooks and creates atomic "instincts" with confidence scoring. Instincts can evolve into full skills/commands/agents.

- **cmux**: Reference for spawning and coordinating teams of agents in cmux panes. Covers Agent Teams (TeamCreate/SendMessage) for Claude Code agents, and generic cmux commands for other tools (Codex, Cursor CLI).

- **orchestrate-implementation**: Orchestrates parallel coding agents for ticket implementation via cmux. Assembles context from Linear tickets, writes detailed prompts with guardrails, spawns agents in worktrees, monitors progress, relays answers, and cleans up.

- **claude-limits**: Shows real Claude plan usage limits (session/weekly/per-model/monthly extra-usage) by reading the local OAuth token and calling the `/api/oauth/usage` endpoint. Reports actual plan-limit percentages, not log-based estimates. Subscription auth only — not applicable under Bedrock or a raw API key.

### prompts

Reusable starter prompts as skills — encode the boilerplate you'd otherwise paste at the start of every session:

- **`/pr-review <PR>`**: Principal-engineer PR review with cross-repo, cross-PR context. Skips nitpicks; flags over-engineering in both the PR and proposed fixes.
- **`/ticket-kickoff <ID>`**: Gather full context on a ticket (parent/related/blocked-by, multi-repo code, recent PRs) and summarize before writing any code.

### pastila

Encrypted pastebin sharing via [pastila.nl](https://pastila.nl/) (ClickHouse's encrypted pastebin):

- **`/pastila` command**: Upload text, files, or conversation context to get shareable end-to-end encrypted URLs. Also supports decrypting existing pastila URLs. Uses AES-GCM encryption matching the web interface.

### ponytail (third-party, referenced)

Not authored here — referenced via a `github` source in `marketplace.json` pinned to `v4.5.0` (sha `60a75f8`); no code is vendored. Bump the `ref`/`sha` to update. Lazy senior-dev mode (YAGNI, stdlib first). Credit + commands: [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail).

## Plugin Development

When adding a new skill to an existing plugin:

1. Create `plugins/<name>/skills/<skill-name>/SKILL.md`
2. Bump `version` in `plugins/<name>/.claude-plugin/plugin.json` so the plugin system re-caches
3. Document the skill in this file under the plugin's section
4. Run `/reload-plugins` (or `/plugin` to update)

When adding a new plugin:

1. Create directory structure under `plugins/<name>/`
2. Create `.claude-plugin/plugin.json` with manifest
3. Add entry to `.claude-plugin/marketplace.json`
4. Hooks use `${CLAUDE_PLUGIN_ROOT}` variable for relative paths within the plugin

Hook matchers in `hooks.json`:
- `"*"` matches all tools
- `"-"` matches PreToolUse only (before any tool runs)
- `"Edit|Write"` uses pipe for OR matching specific tools

## Installation

```bash
# Add marketplace to Claude Code
/plugin marketplace add https://github.com/mexcool/claude-code-toolkit

# Install a plugin
/plugin install claude-dev-tools@claude-code-toolkit
```
