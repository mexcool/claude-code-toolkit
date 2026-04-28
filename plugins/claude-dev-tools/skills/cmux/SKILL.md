---
name: cmux
description: Spawn and coordinate teams of agents in cmux panes. Use when the user asks for a team, swarm, or parallel agents working together.
---

# cmux

## Claude Code Agent Teams

Agent Teams is a feature which allows Claude Code agents to automatically coordinate between themselves using a shared task list and messaging.

### Requirements

The lead agent (you) must be a Claude Code agent launched via `cmux claude-teams` (optionally with `--resume <session-id>`). Without this step the TeamCreate, SendMessage and TeamDelete tools will be unavailable.

**IMPORTANT: Use Agent Teams by default for Claude Code agents. Only resort to the generic commands below upon user request or if the Troubleshooting steps below fail.**

### Tools

```
1. TeamCreate  → creates team config + shared task list
2. Agent       → spawn each teammate with team_name + name + model
3. SendMessage → communicate with teammates by name
4. TeamDelete  → cleanup when done (shut down teammates first)
```

#### Example

```
TeamCreate({ team_name: "my-team", description: "Build feature X" })

Agent({
  name: "frontend-worker",
  model: "sonnet",
  team_name: "my-team",
  prompt: "You are a frontend developer. Wait for instructions.",
  run_in_background: true
})
```

Teammates:

- Opens in their own cmux panes (visible to the user)
- Show `@team-lead` as the prompt source
- Auto-send idle notifications back to the lead
- Share a task list at `~/.claude/tasks/{team-name}/`

### Communication

- `SendMessage` is required — your plain text output is NOT visible to teammates
- Address teammates by `name`, never UUID
- `"*"` broadcasts to all (expensive, use sparingly)
- Teammates message you automatically; messages arrive as new conversation turns

### Task Coordination

Teams share a task list which can be managed via standard Claude Code team tools:

- `TaskCreate`, `TaskUpdate`, `TaskList`, `TaskGet`, `TaskStop` and `TaskOutput`
- Assign tasks with `TaskUpdate`, setting `owner` to teammate name
- Teammates claim unassigned tasks and mark them completed
- Prefer assigning tasks in ID order (lowest first)

### Shutdown

```
SendMessage({ to: "frontend-worker", message: { type: "shutdown_request" } })
SendMessage({ to: "backend-worker", message: { type: "shutdown_request" } })
# Wait for shutdown response messages from teammates, then:
TeamDelete()
```

`TeamDelete` does not automatically close cmux panes. They have to be cleaned up with `cmux close-surface` documented below.

### Troubleshooting

A common failure is `Failed to create teammate pane: Error: not_found: Surface not found` on agent spawn caused by a stale `tmux-compat-store.json`. Fix with:

```bash
rm ~/.cmuxterm/tmux-compat-store.json
```

This works mid-session in case store is stale or corrupted — no relaunch needed.

## Managing Agents

Agent Team features are only available to Claude Code agents. For other tools like Cursor CLI or ChatGPT Codex, use cmux commands to spawn, interact with and manage agents like:

- ChatGPT Codex: `codex`
- Cursor CLI: `agent --model [model]` (`composer-2-fast`, `gpt-5.4-high`, etc)

### Commands

See `cmux --help` for a full list of commands.

**Pane Management**

```bash
# opens new pane and outputs `OK surface:X pane:X workspace:Z`, use to track agents
cmux new-pane --type terminal --direction right

# check on pane status
cmux surface-health

# clean up unused panes
cmux close-surface --surface surface:N
```

**Sending Commands**

```bash
# send input to panes
cmux send --surface surface:N 'codex "prompt"'

# use this after send, also necessary for commands that requires Enter/Y/N confirmation
cmux send-key --surface surface:N Enter
```

**Coordinating Responses**

```bash
# wait for agent completion (ran by team lead)
cmux wait-for [task]-done --timeout 60

# include in prompt to signal lead agent when done
cmux wait-for --signal [task]-done

# manually read progress if wait-for failed to return a signal after timeout
cmux read-screen --surface surface:N --scrollback --lines 200
```

### Spawning Claude Code in a Pane — Gotchas

When spawning a fresh `claude` (not via Agent Teams) to operate in a specific
working directory:

- **Send `cd` and the launch command as separate `cmux send` calls.** Chaining
  with `&&` through `cmux send "cd <path> && cc-d"` is fragile across quoting;
  two sequential sends + Enter each is reliable.
- **Aliases like `cc-d` may not resolve.** The pane's shell often skips
  interactive rcfiles, so `cc-d` errors with "claude not found in PATH". Use
  the absolute path: `/Users/<user>/.local/bin/claude --dangerously-skip-permissions`
  (or whatever `which claude` reports in your normal shell).
- **`direnv allow` first if the target dir has an `.envrc`.** Worktrees and
  fresh checkouts need the env approved before `claude` inherits required
  vars (API keys, project ids); `direnv: error <path>/.envrc is blocked` in
  the screen output is the tell.
- **Verify with `cmux read-screen` after launch.** Check the bottom status line
  shows the expected branch / dir before sending the kickoff prompt.
