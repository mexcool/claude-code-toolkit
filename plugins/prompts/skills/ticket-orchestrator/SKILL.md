---
name: ticket-orchestrator
description: "Orchestrate a ticket from kickoff through PR review in the herdr TUI, herdr app or Rex. The lead and implementer use the selected CLI (Claude Code or Codex), with independent reviewers in the other CLI. Use when asked to run the implementer/reviewer loop for one ticket or act as a meta-orchestrator supervising ticket leads."
---

# Ticket orchestrator

**Meta-orchestrator.** When asked to supervise ticket leads, follow [parent.md](parent.md). Start one ordinary lead per authorized ticket. Each child gets its own ticket, brief and worktree.

**Ticket lead.** For a single ticket, including one assigned by a parent, follow the loop below. The implementer owns the change. You relay handoffs, settle findings, keep scope focused and take steps that need the user only on their word.

**Choose the lead first.** Default to the CLI running this skill. An explicit lead choice takes precedence. If the user selects the other CLI, start the requested lead using [Starting a lead](parent.md#starting-a-lead) and pass it the original request and constraints. Only that lead claims the ticket and starts its workers.

| Role | Name | Claude-led run | Codex-led run | Job |
|---|---|---|---|---|
| Lead | `<t>-lead` | Claude Fable | Codex Astra | Relay, decide and log |
| Implementer | `<t>-impl` | Claude Opus | Codex Sol | Ticket kickoff, code, PR and CI |
| Reviewer | `<t>-rev` | Codex Sol | Claude Opus | Kickoff review and PR review, read-only |
| Blind reviewer | `<t>-blind` | Codex Sol | Claude Opus | Independent PR review, first round from the ticket and PR alone |
| Consequences reviewer | `<t>-cq` | Claude Sonnet | Claude Sonnet | One read-only report on who is worse off, without the plan |

`<t>` is the lowercase ticket id (`proj-123`). Use the same name for each pane, agent and session. Log the chosen lineup at setup.

## Model selection

For a Codex parent or ticket lead, run `<skill-dir>/scripts/latest-codex-model.sh astra`. For a Codex implementer or either Codex reviewer, run the same script with `sol`. It prints the newest listed release of that family. Pass the resulting slug with `-m` when starting the session. If lookup fails, resolve the catalog error or get the user's choice before launching that role. Claude's `fable`, `opus` and `sonnet` aliases track the latest releases. An explicit role-specific model takes precedence.

An already-open chat keeps its active model. For a Codex lead or parent on a different model, have the user select the resolved Astra in `/model` before starting, unless they chose the current model for that role. For an existing Claude lead on another model, mention the Fable default once.

**herdr, Rex or the herdr app.** Make every pane and agent call through `mux.sh` (`<skill-dir>/scripts/mux.sh`; run it with no arguments for its commands). It uses herdr when `HERDR_ENV=1`, else Rex when `REX_SESSION` is set, else the herdr app (herdr-core, `hc`) when `HC_TERMINAL_ID` is set, so this skill reads the same under all three. One difference: herdr reads an agent's state from its screen, while under Rex and the herdr app the agent reports its own state. The app has no panes of its own, so a worker is a terminal named by a `mux.name` label. `name-self` names your tab with a `tab.name` label, which the app's `tab-names` mod ([herdr-extensions](https://github.com/mexcool/herdr-extensions/tree/main/tab-names)) turns into the tab's name. Without that mod the tab shows your session title until you exit, and keeps its number as its name.

## Setup

0. **Use a clean, dedicated worktree.** `git rev-parse --git-dir` must differ from `git rev-parse --git-common-dir`, and `git status` must be clean. Start Claude with `claude --worktree --model fable -n <t>-lead`, or Codex with `codex --no-daemon --worktree -m <resolved-astra>`, inside the intended mux pane. For an existing clean linked worktree, omit `--worktree`. The Codex lead needs the pane's environment, access to the mux socket and write access to `~/ticket-orchestrator/`. For a workspace-write sandbox, create that directory and include `--add-dir ~/ticket-orchestrator` when launching Codex.
1. Run `mux.sh name-self <t>-lead <t>` to name the pane and tab. If it fails, resolve the mux context before claiming the ticket. For a Codex lead, set the thread title to `<t>-lead` with the title tool when available, or use `/rename <t>-lead` in the idle CLI.
2. Check Claude usage with `claude-limits` when installed. In a symlinked toolkit checkout, either lead can run `uv run <toolkit>/plugins/claude-dev-tools/skills/claude-limits/scripts/claude-limits.py`. If usage is unavailable, ask for the user's budget decision before starting paid work. Do not start into paid overage without their word.
3. Make `~/ticket-orchestrator/<TICKET>/` and start `log.md` with one line per event, time from `date -u`.
4. **Claim the ticket.** Assign it to the user and set it In Progress, unless it already is. Log it.
5. Run `mux.sh columns <worktree>` for the implementer and reviewer pane ids. Start each role from the table in the shared worktree. Use the launch sequence for that worker's CLI, including for the two PR-stage reviewers:

   ```bash
   # Claude worker
   mux.sh start <pane> <name> claude "<claude-cmd> --model <model> -n <name>"
   # Codex worker
   mux.sh start <pane> <name> codex "<codex-cmd> -m <model>"
   mux.sh send <name> "/rename <name>"
   ```

   `start` types into the pane's interactive shell, waits for the agent to be ready and names the pane and agent. Use the literal value of `ORCH_CLAUDE_CMD` or `ORCH_CODEX_CMD` when set (aliases are expanded by that shell). The stock commands are `claude --dangerously-skip-permissions` and `codex --dangerously-bypass-approvals-and-sandbox`. Use one model flag per worker. Honor a model already set by the launch command unless the user requests a different one.

6. Write `brief-impl.md` and `brief-rev.md` from [briefs.md](briefs.md), with literal paths and names. Send each one line, as in Protocol: the implementer starts the kickoff. The reviewer starts **prep**: it reads the ticket and the code before it sees the plan, so it has its own view, and writes `prep.md`.

## Protocol

- **Every handoff is a file in the folder,** and each message you send names the file to write. The worker prints the file in its chat word for word, because the user reads the chats, then ends its turn. Workers message nobody: every finding passes your filter.
- Send each brief once with `mux.sh prompt <worker> "[<t>-lead] <one line>" 3600`. The command submits the prompt and waits for the worker's turn to settle. Dispatch independent workers before waiting for their results.
  - **Claude lead:** use Bash's background-task mode. End your turn after dispatch. Task completion wakes you.
  - **Codex lead or parent.** Wrap each blocking command in `<skill-dir>/scripts/codex-wait.sh <absolute-result-file> <command> <args...>`, for example `codex-wait.sh <dir>/wait-impl-1.log <skill-dir>/scripts/mux.sh prompt <worker> "<message>" 3600`. Use a fresh result path per wait. Start it in a PTY with a short `exec_command` yield. Keep its session id for cancellation, and end your turn once the waits are running. Keep the Codex CLI open. The wrapper saves the command's output and exit status, then uses `codex queue` to wake this thread. On wake, read the result and check the handoff. If another wake already advanced that handoff, continue from the log. Use this for grace waits and parent inbox watches too.
  - If `codex queue`, its writable local queue, or `CODEX_THREAD_ID` is unavailable, run the blocking command directly. Use this fallback for a restricted shell until queue access is verified. Keep the turn open and collect its session with `write_stdin` using empty input and a long yield. The shell waits between tool calls. On session restart, read saved results and handoffs before sending anything again.
- **When it returns, key on the file**, never on `idle` versus `done`. herdr reads the agent state from the screen, so it can be wrong. And under herdr, `done` versus `idle` means "nobody has looked at the pane yet" versus "someone has", not "finished" versus "not finished". If the worker has settled and its expected file exists, go on. A `working` result at the timeout is a check-in. Continue the settled wait before sending another prompt. If the state is `blocked`, `mux.sh read <worker>` now. Otherwise, run `mux.sh wait <worker> working 120` with the same wait procedure for a 2-minute grace window. If the worker starts working again (Codex can settle between its own turns), go back to a settled wait (`mux.sh wait <worker> settled 3600`). If it stays settled for 2 minutes with no file, read the pane, then decide or tell the user. This rule also covers a prompt that never started a turn. A 1-hour timeout is a check-in, not an alarm. Never resend blindly.
- **Message a worker only after its turn ended.** On Codex, Enter during a turn steers that turn.
- **No dialogs in any pane:** no AskUserQuestion, and no plan mode for the implementer. `mux.sh prompt` refuses a pane with a dialog (`blocked`), and the loop then waits on the user. Questions go into the files.

## The loop

1. **Kickoff.** The implementer writes `ticket-kickoff.md`. It ends with a **Contract**: the files it will change, the rough diff size, the "Done when" items this PR closes with the check for each, and what is out of scope. The reviewer writes `kickoff-review-N.md`. Each finding has an id, a severity, evidence and a minimum fix, and the file ends with a verdict.
2. **Sort every finding** into `lead-kickoff-N.md`, with your decision on each one:
   - **must-fix** (wrong behaviour, a ticket requirement not met, security): relay.
   - **should-fix**, if it is small and inside the contract: relay.
   - **user call**: real, and somebody pays for it (a user waits, an operator loses a signal, old data looks current), but the fix is outside the contract or the plan accepted the cost. Do not relay it and do not drop it: log it with who pays and for how long, for the user to decide.
   - **drop**: nits, style, "you could also", edge cases that cannot happen, new abstractions, extra docs, speculative tests (a test that checks a contract item or measures an accepted risk is not speculative). List the drops in the file and in the log.

   The implementer updates the kickoff in place. It answers in `kickoff-response-N.md`: **accepted** (what changed) or **push back** (with evidence). Pushing back is normal.
3. **Later rounds:** the reviewer rechecks only its open findings and what changed. It raises a new finding only if it is must-fix. Allow one exchange per disagreement. After that, decide from the ticket and the code.
4. **When a stage ends:** at LGTM, at a round with nothing to relay, or when a point comes back without new evidence. There is no hard limit. If a stage reaches round 3, log why and tell the user.
5. **User decisions that add scope** go out with your next relay, not in the middle of a review, so the reviewer reviews one version.
6. **The kickoff is agreed** when both workers agree. There is no plan gate for the user. Tell the user, and list the open user calls. Decide the blind reviewer and the consequences reviewer now, before any code exists, and log it: both are on unless the contract is docs only or tests only. The implementer builds, opens the PR ready for review, gets CI green, and writes `pr-ready.md` (links, the output of each contract check, any difference from the contract and why).
7. **PR review:** the same loop with `pr-review-N.md`, `lead-pr-N.md` and `pr-response-N.md`. The reviewer also checks the PR against the agreed kickoff: anything agreed but missing, anything built but not agreed. Do not drop a finding only because it contradicts the ticket, the contract or an earlier decision: drop it with evidence, or make it a user call.
8. **Blind reviewer**, unless you skipped it at step 6 and the PR still matches that docs- or tests-only contract. When `pr-ready.md` lands, make `<dir>-blind/` next to the loop folder (no path to the plan), write `brief-blind.md` there from [briefs.md](briefs.md), split the reviewer's pane down (`mux.sh split-below <rev-pane> <worktree>`), start `<t>-blind` there using its CLI and model from the table, and send the brief with the reviewer's round 1. It then runs the loop like the reviewer, writing `pr-blind-N.md` in its folder. Relay once per round, when both reviews are in, and stop sending rounds to a reviewer with no open findings. If the blind reviewer stalls past the grace window, go on without it and log it. The stage ends when both are done.
9. **Consequences reviewer**, on and off together with the blind reviewer. It has another job than the two reviewers, and another model: it does not look for bugs, it reports who is worse off by each behaviour the PR changes. When `pr-ready.md` lands, check the usage limits again (Setup 2), write `brief-cq.md` in `<dir>-blind/` from [briefs.md](briefs.md), split the implementer's pane down (`mux.sh split-below <impl-pane> <worktree>`), start `<t>-cq` there using its CLI and model from the table, and send the brief. It writes `pr-consequences.md` once: no verdict, no later rounds. Sort each entry like a finding; most are user calls. Close its pane once the report is sorted. If it stalls past the grace window, go on without it and log it.
10. **Done** means: the "Done when" items that this PR owns are met, and the repo's merge gate is green. A silent reviewer does not mean done.

## Steps that need the user

These are merge, apply, deploy, test pages, product decisions, and posts outside the PR (tracker, chat, GitHub reviews). Ask in plain text. Before you ask for a merge, read `gh pr diff` yourself and check it against the contract. The reviewer's LGTM does not replace your own read. Get the user's answer on each open user call first: fix now, a ticket, or accept. When the user says yes, give the step to the implementer in `lead-ops-N.md` with stop conditions:
- pin the reviewed head: `gh pr merge --squash --match-head-commit <sha>`, never `--admin`;
- give the expected plan summary: `terraform plan -out`, then apply that saved plan;
- stop at the first failure;
- report in `ops-N.md`.

The implementer owns these operations in the checkout. A test page starts an escalation clock. Send it only when the person who must acknowledge it is at the screen, and give them the deadline at once.

**A PR that must not close a multi-PR ticket:** Linear links a bare ticket id in a branch name, title or body as "closes", and the merge then closes the ticket. Tell the implementer, in the brief, to make the first line of the PR body `Part of PROJ-123` and to keep the id out of the branch name. "Part of" is one of Linear's contributing words (also "ref", "towards", "contributes to"), so the link is `contributes` and the id can stay in the title. When the PR opens, check the issue's attachment `metadata.linkKind`. If it is `closes`, fix the body and check again.

## When a parent started you

Your first prompt or brief names a **parent**: another session that runs several loops and stands between you and the user. Its side is in [parent.md](parent.md).

- Each step that needs the user goes to the parent, not to the user. Write the question and wait for the answer.
- Report one line at each event: started (where you run, your workers), kickoff agreed, PR ready, review done, each step that needs the user, done. Also one line for a finding outside your ticket; keep it out of your PR.
- The channel is the one the brief names. A file: append one line with the UTC time from `date -u` (never from memory), the ticket id, the event word, one sentence, and the path of the file with the details. Under the herdr app you can instead send the same line with `hc send <parent> "<line>"`.
- An answer is a file or a message with what is authorized, what is not, and stop conditions. Do what it says and no more. An approval covers the head and the content it names: a new head or a new push needs a new answer.
- Before a merge question, say in the line whether a review bot or a person approved, and whether `mergeable` is clean.

## End

If proof needs time (for example a soak week), use `follow-up-check` when available in Claude Code. A Codex lead can use an available reminder tool for the authorized check. If scheduling is unavailable, record the due time and check in the handoff and tell the user it still needs scheduling.

Finish or cancel the outstanding waits before closing worker panes (`mux.sh close <pane>`). In Claude use `TaskStop` for a pending background task. In Codex, collect completed sessions and interrupt any remaining wait in its own terminal. Worker sessions stay on disk. Give the user the result and the open items. Name the class of problem the ticket belongs to, and if one follow-up would remove the class, propose it; don't build it.

## Gotchas

- **An isolated Claude lead** (started with `--worktree`) cannot run some Bash calls. Its harness refuses a call that puts a runtime value (`$VAR`, `$(…)`) next to `herdr` or `git`, or that pipes into an interpreter. Use literal ids, one plain command per call, and put scripts in files. It also refuses git in another repo's checkout, so the implementer runs those steps.
- **Codex started through its app-server daemon** runs shell commands in the daemon's environment, so pane `--env` variables are missing. Briefs must carry literal paths and names.
- **`herdr pane move`** stops every open wait on that agent (`agent_not_running`). Start the waits again after a move.
- **Do not wait for an agent with a screen regex.** `herdr pane wait-output` also matches text already on the screen, and a shell prompt can use the same glyph as the agent (`❯`). `mux.sh start` waits on the agent state.
- **A slash command** sent to a busy Claude pane arrives as plain text. Send `/rename` only when the pane is idle. A Claude lead that needs to rename itself can run this in the background: `mux.sh wait <t>-lead settled && mux.sh send <t>-lead "/rename <t>-lead"`.
- **Read files, not panes.** `mux.sh read` shows stale lines when a Codex pane is scrolled.
- **Claude phone pings:** PushNotification reaches the phone only if mobile push is on in `/config`. Check this at setup. Without it, `log.md` and the chats are the record.
