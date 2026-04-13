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

### pastila

Encrypted pastebin sharing via [pastila.nl](https://pastila.nl/) (ClickHouse's encrypted pastebin):

- **`/pastila` command**: Upload text, files, or conversation context to get shareable end-to-end encrypted URLs. Also supports decrypting existing pastila URLs. Uses AES-GCM encryption matching the web interface.

## Plugin Development

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
