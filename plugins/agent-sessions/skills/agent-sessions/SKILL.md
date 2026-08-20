---
name: agent-sessions
description: "Find, search, and resume Claude Code and Codex agent sessions after a terminal or multiplexer dies. Use when asked to recover lost agents, find which session worked on a ticket or PR, list what ran recently, or produce copy-paste commands to cd into a worktree and resume the right session."
version: 0.1.0
---

# Agent Sessions

Recover parallel agents after the terminal dies. Both CLIs keep every session as a JSONL transcript on disk, so nothing is ever lost — the problem is only ever *finding* the right id and the cwd it belongs to.

## The one rule

**Check for a live process before you resume anything.** A multiplexer dying usually does not kill the agents underneath it. Two processes on one transcript corrupt it.

- Process alive → **reattach** the multiplexer.
- Process gone → **resume** with the printed command.

`list` makes that split for you.

## Usage

Run the script from this skill's own directory — the agent is told that base path when the skill loads, so use it rather than a hardcoded location:

```bash
S=<this-skill-dir>/scripts/agent-sessions.py

uv run $S list                       # last 24h, split live vs resumable (default)
uv run $S list --hours 72 --repo myrepo
uv run $S list --json                # machine-readable

uv run $S find PROJ-123              # which transcript owns this ticket / PR / string
uv run $S find 4821 --hours 720 --top 5

uv run $S show 9f3c1a2b --limit 5    # read a transcript's human turns (id prefix ok)
```

## What `list` prints

```
LIVE under herdr — reattach with `herdr`, do NOT resume:

  claude  working  ws:t5   Refactor the payment retry path
  codex   idle     ws:t4   my-feature-worktree

RUNNING (2) — process still up, reattach:

  [claude] PROJ-123  pid 41207  4m ago
    9f3c1a2b-…  ·  /home/you/code/myrepo

RESUMABLE (6) — last 24h, newest first:

  # PROJ-456 [fix/checkout-timeout] · 2h ago · 1.9 MB
  # last: prek failed..
  cd /home/you/code/myrepo/.worktrees/checkout && \
  claude --resume 4d81ba07-…
```

Two blocks, one decision: anything under LIVE/RUNNING gets **reattached**, anything under RESUMABLE gets the **command below it**, pasted into a shell.

Relay those command lines verbatim — they are the deliverable, and the user copies them by hand. Each carries the branch and the last human turn so sessions are tellable apart.

The `cd` is **required**: `codex resume` filters its picker by cwd, and Claude keys sessions by the directory the session *started* in.

If the user launches these CLIs through wrapper aliases (extra flags, a different auth env), set `AGENT_SESSIONS_CLAUDE_CMD` / `AGENT_SESSIONS_CODEX_CMD` and the printed lines use those instead. Aliases are fine here — the lines are pasted into an interactive shell.

## Where things live

```
~/.claude/projects/<slugified-start-cwd>/<session-uuid>.jsonl
    └── <session-uuid>/subagents/agent-<id>.jsonl     # subagent transcripts
~/.codex/sessions/YYYY/MM/DD/rollout-<iso-ts>-<uuid>.jsonl
~/.codex/session_index.jsonl                          # id → thread_name, partial
```

## Multiplexers

Agents are usually hosted in a multiplexer — tmux, cmux, or herdr. When one dies its agents normally survive as orphaned processes, so a failing `tmux ls` is not proof the work is gone. Check `ps` first; `list` does.

`list` folds in `herdr agent list` when that binary is present. There, `herdr tab list` shows every tab and marks dead agents as `agent_status: "unknown"` — those are the ones that need resuming.

## Gotchas

Learned the hard way; each one produced a wrong answer first.

**The slug is the *start* cwd, not the work cwd.** A session that began in the repo root and later moved into a worktree still files under the root's slug. Resume from the start cwd. Conversely a worktree-slugged session whose directory was since deleted still resumes — from the parent repo.

**Codex filenames contain dashes in the timestamp.** `rollout-2026-01-07T10-33-48-<uuid>.jsonl` — never `split("-")` for the id. Anchor a UUID regex at the end of the stem. A truncated id silently fails to match the live process, so a running agent looks dead.

**Rank by mention count, not mtime.** Long-running sessions drift across topics; a ticket's real owner is usually the transcript that names it hundreds of times, not the one touched most recently. That is what `find` does.

**Labels lie.** A tab named after one ticket may have opened as a review of a different PR, and a session may have moved on to a successor ticket. Confirm against the opening turn and the branch, and say so when they disagree.

**Not every `ABC-123` is a ticket.** Transcripts quote model names, other teams' tickets, and unrelated PR numbers. A ticket named in the *opening* turn is the subject; one merely frequent may not be.

**Codex and skills inject `role: user` turns.** The AGENTS.md block and skill preambles are not the human talking. Filter them or the "first message" is boilerplate.

**Transcripts reach 100 MB+.** Never read one whole, and never hand one to a subagent to read. The script bounds itself to a head and tail read; use `show` or `find` instead of `cat`.

**Subagent transcripts cannot be resumed.** They nest under the parent session id. Resume the parent, or start fresh in the worktree. A worktree named `agent-<hex>` *is* a subagent's — there is no top-level project dir for it.

**`grep` may be aliased to another implementation** (for example `ugrep`), which parses flags differently and fails on `grep -rl -i`. Use `command grep` in ad-hoc shell — which is why the script counts matches in Python instead.

**Set the launch-command vars in `.zshenv`, not `.zshrc`.** The skill is normally run by an agent through a tool call — a non-interactive shell, which sources `.zshenv` only. Put `AGENT_SESSIONS_CLAUDE_CMD` in `.zshrc` and it is silently ignored, so the printed lines fall back to a bare `claude` / `codex` with no hint why.

**Live agents may carry no id on argv.** `claude --resume` (interactive picker) and `claude --worktree` show no session id in `ps`. Match those on `/proc/<pid>/cwd` instead.
