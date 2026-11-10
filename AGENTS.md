# Agent guidance

This file guides any coding agent working in this repository. It is read as `AGENTS.md` by Codex and as `CLAUDE.md` by Claude Code (same file — `CLAUDE.md` is a symlink).

## Public Repository

This is a **public open-source repo**. All content is visible to anyone. Follow these practices:
- Never commit secrets, API keys, tokens, or credentials
- Use generic examples (e.g., `PROJ-123`) — no internal project names, team prefixes, or real ticket IDs
- No internal URLs, Slack channels, employee names, or company-specific references
- No personal shell aliases or machine paths — a skill must run for a stranger. Make the launch command configurable (env var or flag) with a stock default, rather than hardcoding a wrapper alias
- Review diffs before committing for accidental leaks

> **Agents: this bites hardest when a skill is distilled from real work.** The session you learned the lesson in is full of real ticket IDs, PR numbers, repo names, and hostnames, and they get copied across verbatim as "examples". Before committing, scrub the diff:
>
> ```bash
> git diff --cached | grep -niE '<your-org>|<your-ticket-prefix>-[0-9]|<your-domain>|/Users/|/home/[a-z]'
> ```
>
> Rewrite each hit as a placeholder — `PROJ-123`, `myrepo`, `~/…`. Keep the *lesson*, drop the *instance*.

## Project Overview

This is a Claude Code plugin marketplace containing reusable plugins for enhanced development workflows. Plugins provide skills, hooks, commands, and agents that extend Claude Code's functionality.

The plugins are authored for Claude Code, but the **agent-agnostic skills** (see the install list below) are also consumable by **Codex**, which reads skills from `$CODEX_HOME/skills`. `install-codex.sh` symlinks those skills there — one source of skill files, two agents, no copies. See [Installation](#installation).

This repo has no ticket tracker. Commit and PR titles use conventional-commit style (`feat(pr-review): …`, `chore(prompts): …`), not ticket IDs — skip the ticket steps of any global git workflow.

## Merging PRs

Merge with the owner's noreply address, `mexcool@users.noreply.github.com`, as both author and committer. GitHub's merge button and `gh pr merge --author-email` reject that address for this account, so merge from git instead:

1. Make the PR branch one commit on top of `origin/main`, with the subject `<PR title> (#N)`: `git fetch origin main && git reset --soft origin/main && git commit`, then `git push --force-with-lease`. The owner's git config already uses the noreply address and signs commits; the ruleset rejects unsigned ones.
2. Fast-forward `main` to that commit: `git push origin <sha>:main`. The owner bypasses the review rule, as with `gh pr merge --admin`. GitHub marks the PR merged and deletes the branch. If the push is refused as non-fast-forward, `main` moved: redo step 1.

## Repository Structure

```
.claude-plugin/marketplace.json    # Marketplace manifest listing available plugins
install-codex.sh                   # Symlinks agent-agnostic skills into Codex ($CODEX_HOME/skills)
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

- **follow-up-check**: Schedules a check on shipped work that needs data that does not exist yet. A Linear comment posted now points at a secret gist holding the check plan, scripts and baselines; a native Linear `issueReminder` pings the user on the due date (optionally also in Slack). An optional one-shot cloud routine (`/schedule`) re-posts the comment on the due date for people following the issue. `scripts/follow-up.py` prints a weekday due time with a transcript-expiry warning (`due`) and the session facts to resume (`session`, from `CLAUDE_CODE_SESSION_ID`). Kept with the Claude-specific tools because it relies on Claude Code sessions and routines.

- **ticket-orchestrator**: Lead role for one ticket run by two herdr workers: a Claude implementer (ticket kickoff, code, PR) and a Codex reviewer (kickoff review, PR review), all in one worktree and one tab. Handoffs are files in `~/ticket-orchestrator/<TICKET>/`; the lead sends each message with a background `herdr agent prompt --wait`, so herdr's screen-detected agent state wakes it when the worker's turn ends (the send is also the stall watchdog; the lead keys on the handoff file plus a 2-minute grace window, never on idle versus done), and `scripts/wait-agent.sh` waits for herdr's agent detection at startup. Setup refuses to run outside a dedicated worktree, and claims the ticket (assigned to the user, In Progress). The lead sorts findings (must-fix / should-fix / drop) to stop scope growth, and gives steps that need the user (merge, apply, test page) to the implementer only after the user says yes, with stop conditions. `briefs.md` holds the worker brief templates. Launch commands come from `ORCH_CLAUDE_CMD` / `ORCH_CODEX_CMD`. Kept with the Claude-specific tools because the lead relies on Claude Code background tasks and `/rename`.

### agent-sessions

Agent-agnostic (exported to Codex):

- **agent-sessions**: Finds, searches, and resumes Claude Code and Codex sessions after a terminal or multiplexer dies. Reads the on-disk JSONL transcripts, matches them against live processes, and prints copy-paste `cd … && <cli> --resume …` commands. Subcommands: `list` (live vs crashed vs resumable), `find <pattern>` (rank transcripts by mention count), `show <id>` (read a transcript's human turns).

  Scans both `~/.claude/projects` and `~/.codex/sessions` on every run, whichever agent invokes it — a dead terminal loses both at once. Crashed Claude sessions come from the `~/.claude/sessions/<pid>.json` files Claude leaves behind when a process dies without a clean exit; Codex keeps no equivalent. Launch commands in the printed lines default to stock `claude` / `codex`; override with `AGENT_SESSIONS_CLAUDE_CMD` / `AGENT_SESSIONS_CODEX_CMD` for wrapper aliases.

### prompts

Reusable starter prompts as skills — encode the boilerplate you'd otherwise paste at the start of every session:

- **`/pr-review <PR>`**: Principal-engineer PR review with cross-repo, cross-PR context. Skips nitpicks; flags over-engineering in both the PR and proposed fixes.
- **`/ticket-kickoff <ID>`**: Gather full context on a ticket (parent/related/blocked-by, multi-repo code, recent PRs) and summarize before writing any code.
- **`/kickoff-review <ID>`**: Second-agent review of a pasted kickoff before implementation — simplicity and scope creep, what must land first, checked against the ticket and the latest `origin/main`. Review only; sets expectations for the reply and PR rounds.

### reference-docs

Agent-agnostic (exported to Codex). Reference books/docs published for LLM consumption (llms.txt style), each as a skill that embeds the text's section map and fetches only the sections relevant to the conversation — never the full text:

- **inference-engineering**: Grounds model-serving and inference-optimization answers in *Inference Engineering* (Philip Kiely, Baseten Books, 2026). Covers inference engines, quantization, speculative decoding, caching, GPU hardware, modality-specific serving, and production infra. Fetches per-section markdown from `baseten.co/inference-engineering/book/…` on demand.

To add another book: check it publishes stable per-section URLs (an `llms.txt` index is the tell), then add a sibling skill whose SKILL.md holds the section map and fetch instructions.

### cli-dev

Agent-agnostic (exported to Codex). Skills for designing and reviewing CLIs that coding agents drive via shell execution:

- **axi**: Agent eXperience Interface — ergonomic standards for agent-facing CLI tools. Use when building, modifying, or reviewing any CLI an agent will call.
- **cursor-cli-dev**: Designs or reviews CLIs for reliable non-interactive use: flags over prompts, layered `--help` with examples, stdin/pipelines, fast actionable errors, idempotency, dry-run.

### gist

Agent-agnostic (exported to Codex):

- **gist**: Conventions for GitHub Gists as an internal pastebin via the `gh` CLI — creating, sharing, reading, and piping gist content into other tools.

### obsidian-helper

- **`/done` command**: Summarizes the current session and saves it as a note in the Obsidian work vault.

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

When adding a rule to an existing skill (most often a checklist such as `pr-review`), keep the list from growing forever. Add a line only when all three are true:

1. A real run of the skill missed something.
2. The current wording should have caught it and did not.
3. The new line has no domain words: it names the kind of mistake, not the case.

Merge the new line into an existing bullet, and remove a line if you can. Keep each skill to about one screen. "Check each input's unit and bound" passes this test; "count unpriced rows per key" does not.

When adding a new plugin:

1. Create directory structure under `plugins/<name>/`
2. Create `.claude-plugin/plugin.json` with manifest
3. Add entry to `.claude-plugin/marketplace.json`
4. Hooks use `${CLAUDE_PLUGIN_ROOT}` variable for relative paths within the plugin
5. If the plugin's skills are agent-agnostic (no Claude-only features — hooks, `/compact`, Agent Teams, the usage endpoint), add its name to `AGENT_AGNOSTIC_PLUGINS` in `install-codex.sh` so Codex gets them too. Keep skills self-contained: a portable skill must not depend on `${CLAUDE_PLUGIN_ROOT}` or Claude-only tools.

Hook matchers in `hooks.json`:
- `"*"` matches all tools
- `"-"` matches PreToolUse only (before any tool runs)
- `"Edit|Write"` uses pipe for OR matching specific tools

## Installation

### Claude Code (plugin marketplace)

```bash
# Add marketplace to Claude Code
/plugin marketplace add https://github.com/mexcool/claude-code-toolkit

# Install a plugin
/plugin install claude-dev-tools@claude-code-toolkit
```

### Codex (agent-agnostic skills)

Codex has no marketplace; it reads skills from `$CODEX_HOME/skills` (default `~/.codex/skills`). Symlink the agent-agnostic skills there:

```bash
./install-codex.sh   # idempotent; re-run after pulling new skills
```

Installs `agent-sessions`, `axi`, `cursor-cli-dev`, `gist`, `inference-engineering`, `kickoff-review`, `pr-review`, `ticket-kickoff`. `claude-dev-tools` is Claude-specific (usage endpoint, `/compact`, hooks, Agent Teams) and intentionally not exported; `obsidian-helper` / `pastila` are slash-commands, not skills.
