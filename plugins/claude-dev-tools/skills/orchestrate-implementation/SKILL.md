---
name: orchestrate-implementation
description: >
  Orchestrate parallel coding agents for ticket implementation via cmux.
  Spawns Opus (latest) agents in worktrees, writes detailed prompts with
  context pointers and guardrails, monitors progress, relays answers, and
  cleans up. Use when the user asks to implement 1+ tickets with coding
  agents, or says "orchestrate", "spawn agents for", "implement these
  tickets".
arguments:
  - name: tickets
    description: "Space-separated ticket IDs (e.g., PROJ-123 PROJ-456)"
    required: true
---

# Orchestrate Implementation

You are the orchestrator. You do NOT implement -- you steer coding agents
that do. Your job: context assembly, prompt writing, monitoring, and
decision relay.

## Phase 1: Context Assembly

For each ticket:
1. Fetch the full ticket from Linear (include relations)
2. Identify all relevant source files, spec docs, session logs, and related tickets
3. Identify dependencies between tickets (which blocks which)
4. Read key files yourself so you can answer agent questions accurately

## Phase 2: Prompt Writing

Write one prompt per ticket to a temp file (`/tmp/<ticket_id>_prompt.txt`).

**Critical formatting rules** (shell expansion safety):
- NO backticks in prompt files -- they break `$(cat ...)` expansion
- Use `--` instead of em-dashes
- Keep markdown formatting (`**bold**`, `##`) but avoid code fences

Each prompt MUST follow this structure:

```
You are working on ticket <ID>: <title>.

## Your ticket
Read the full ticket on Linear: use the Linear MCP tool to get <ID>
(include relations). It has the complete spec.

## Context pointers -- read ALL of these before doing anything
<numbered list of specific files with brief description of why each matters>

## What you are building
<numbered list of concrete deliverables>

## Dependencies
<what this ticket depends on, what is being built in parallel by other agents>

## Approach
Read the code, context docs and ticket (and related tickets) thoroughly.
Understand what you need to do and why. Ask me any questions to clarify
your understanding.

DO NOT start implementing until we have aligned. This is a HARD
REQUIREMENT. The workflow is: explore -> ask questions -> plan -> implement.
Do not skip steps.

Once all is clear, enter plan mode and write an implementation plan with
references to specific code lines, function signatures, dataclass
definitions, and test patterns. Only after the plan is reviewed should
you begin coding.

## Guardrails
<ticket-specific boundaries: what NOT to touch, what stays as-is>

## Standards
- Pre-commit must pass (run the project's pre-commit command)
- Write thorough tests following existing patterns
- Follow conventions in the project's CLAUDE.md and any steering files
```

## Phase 3: Agent Spawning

Use cmux to spawn agents. Refer to the `/cmux` skill for full command
reference (pane management, sending commands, reading output).

Each agent gets its own pane and worktree. Use the **latest Opus model**
(currently Opus 4.6) for implementation agents. Always use **interactive
TUI mode** (NOT headless `-p`) so the user can watch agent progress in
real time.

**Per-agent spawning workflow:**

1. Create a pane with `cmux new-pane` — note the `surface:N` from output
2. Send: `cd <repo> && claude --dangerously-skip-permissions --worktree`
3. Wait for TUI to show the input prompt (the `---` line with `>`)
4. Send the prompt text (read from file to avoid quoting issues):
   `PROMPT=$(cat /tmp/<ticket>_prompt.txt)` then send `$PROMPT` to the surface

**Track this table for each agent:**

| Agent | Ticket | Surface | Worktree name | Status |
|-------|--------|---------|---------------|--------|

## Phase 4: Monitoring

Set up a monitoring loop via ScheduleWakeup (~2-3 min intervals).

On each check, read agent output using `cmux read-screen` (see `/cmux`
skill for full syntax).

**What to look for:**
- **Agent asked questions**: Read full questions from scrollback,
  answer based on your context knowledge, relay via `cmux send`
- **Agent waiting idle**: Nudge with next step (e.g., "run pre-commit",
  "run tests")
- **Agent stuck on error**: Read the error, diagnose, send fix instructions
- **Interface dependencies**: When one agent defines an interface that
  another needs, relay the concrete signatures/dataclass shapes immediately
- **Agent finished**: Verify pre-commit passed, tests pass, note completion

## Phase 5: Cleanup

When an agent completes or is killed:
1. Close its cmux surface (see `/cmux` skill for pane cleanup commands)
2. List all worktrees: `git worktree list`
3. Remove stale/completed worktrees: `git worktree remove --force <path>`
4. Clean up orphaned worktrees from failed spawns too

**Always clean up ALL worktrees created during the session**, including
from failed spawn attempts (each `--worktree` flag creates one even if
the session crashes).

## Decision Authority

**Answer agent questions directly when:**
- The answer is in a spec doc, ticket, or previous discussion
- It is a reasonable default (e.g., starting constant values)
- It is about interface contracts between parallel agents

**Escalate to the user when:**
- The question changes scope or architecture
- You are genuinely unsure about intent
- The agent pushes back on a design constraint
