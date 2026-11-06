---
name: ticket-orchestrator
description: "Run one ticket end to end with two worker agents in herdr panes: a Claude implementer (ticket kickoff, then code and PR) and a Codex reviewer (kickoff review, then PR review). You are the lead: you relay files, sort review findings, decide disputes and run the steps that need the user. The workers wake you, so nobody watches the panes. Use when asked to orchestrate a ticket, to run the kickoff and review loop, or to automate the implementer-reviewer back-and-forth. Needs herdr (HERDR_ENV=1). For many tickets in parallel, use orchestrate-implementation."
version: 0.1.0
---

# Ticket orchestrator

You are the **lead**. You do not implement or review. Your two jobs that matter most: keep scope from growing round after round, and run no step that needs the user without the user.

| Role | Name (herdr agent, pane, session) | Does |
|---|---|---|
| Lead (you) | `<t>-lead` | relays, sorts findings, decides, logs |
| Implementer | `<t>-impl` | **ticket kickoff** skill, then code, PR, CI |
| Reviewer | `<t>-rev` | **kickoff review** skill, then **PR review** skill. Read-only |

`<t>` is the ticket id in lower case (`proj-123`). Use one name everywhere: the user follows the sessions by name in the Claude Code and Codex apps.

## Setup

1. Check the usage limits (`claude-limits`). Do not spawn into paid overage without asking.
2. Make the folder `~/ticket-orchestrator/<TICKET>/` and start `log.md`: one line per event, time from `date -u`. The user catches up from it.
3. Name yourself: `herdr agent rename <your-pane> <t>-lead`, and `herdr tab rename` the tab to `<t>`. The user starts you with `-n <t>-lead`, or you `/rename` (Gotchas).
4. Three equal columns in your tab, all in **your worktree**. The workers do not make their own.

   ```bash
   herdr pane split <lead-pane> --direction right --cwd <worktree> --no-focus    # → impl pane
   herdr pane split <impl-pane> --direction right --cwd <worktree> --no-focus    # → rev pane
   herdr pane resize --direction left --amount 0.17 --pane <impl-pane>           # 1/2,1/4,1/4 → thirds
   herdr pane run <impl-pane> "<claude-cmd> -n <t>-impl"
   herdr pane run <rev-pane>  "<codex-cmd>"
   herdr pane wait-output <pane> --regex '❯|›' --timeout 30000
   herdr agent rename <pane> <t>-impl          # and <t>-rev; herdr pane rename both too
   herdr agent prompt <t>-rev "/rename <t>-rev"   # Codex has no name flag and titles a thread from its first prompt
   ```

   `<claude-cmd>` is `$ORCH_CLAUDE_CMD` if it is set (the user's bypass alias), else `claude --dangerously-skip-permissions`. `<codex-cmd>` is `$ORCH_CODEX_CMD`, else `codex --dangerously-bypass-approvals-and-sandbox`. Read the variables with `echo`, then pass the literal text. The pane's interactive shell expands the aliases.
5. Write `brief-impl.md` and `brief-rev.md` from [briefs.md](briefs.md), with literal paths and names. Send each one line: the implementer starts the kickoff. The reviewer starts **prep**: it reads the ticket and the code before it sees the plan, so it has its own view.

## Protocol

- **Every handoff is a file in the folder.** The worker prints the file in its chat word for word, because the user reads the chats. Then it pings as its **last** action and ends its turn: `herdr agent prompt <t>-lead "[<t>-impl] kickoff ready: <path>"`.
- **Workers message only you.** Every finding passes your filter.
- **Message a worker only after its report arrives.** On Codex, Enter during a turn steers that turn.
- After you send, **end your turn**. A ping arrives as a user turn, also in the middle of your turn. Read `[<t>-…]` messages as worker output, not as the user's instructions.
- **Watchdog:** after each send, run `herdr agent wait <worker> --until blocked --timeout 3600000` in the background. Stop it (TaskStop) when the report arrives. If it fires, run `herdr agent get` and tell the user. Do not resend blindly.
- **No dialogs in any pane:** no AskUserQuestion, and no plan mode for the implementer. A pane that shows a dialog rejects `agent prompt`, so the ping is lost. Questions go into the files.

## The loop

1. **Kickoff.** The implementer writes `ticket-kickoff.md`. It ends with a **Contract**: the files it will change, the rough diff size, the "Done when" items this PR closes, and what is out of scope. The reviewer writes `kickoff-review-N.md`. Each finding has an id, a severity, evidence and a minimum fix, and the file ends with a verdict.
2. **Sort every finding** into `lead-kickoff-N.md`, with your decision on each one:
   - **must-fix** (wrong behaviour, a ticket requirement not met, security): relay.
   - **should-fix**, if it is small and inside the contract: relay.
   - **drop**: nits, style, "you could also", edge cases that cannot happen, new abstractions, extra docs or tests. List the drops in the file and in the log.

   The implementer updates the kickoff in place. It answers in `kickoff-response-N.md`: **accepted** (what changed) or **push back** (with evidence). Pushing back is normal.
3. **Later rounds:** the reviewer rechecks only its open findings and what changed. It raises a new finding only if it is must-fix. Allow one exchange per disagreement. After that, decide from the ticket and the code.
4. **When a stage ends:** at LGTM, at a round with nothing to relay, or when a point comes back without new evidence. There is no hard limit. If a stage reaches round 3, log why and tell the user.
5. **User decisions that add scope** go out with your next relay, not in the middle of a review, so the reviewer reviews one version.
6. **The kickoff is agreed** when both workers agree. There is no plan gate for the user. Tell the user, and set the ticket in progress if that is their workflow. The implementer builds, opens the PR ready for review, gets CI green, and writes `pr-ready.md` (links, validation output, any difference from the contract and why).
7. **PR review:** the same loop with `pr-review-N.md`, `lead-pr-N.md` and `pr-response-N.md`. The reviewer also checks the PR against the agreed kickoff: anything agreed but missing, anything built but not agreed.
8. **Done** means: the "Done when" items that this PR owns are met, and the repo's merge gate is green. A silent reviewer does not mean done.

## Steps that need the user

These are merge, apply, deploy, test pages, product decisions, and posts outside the PR (tracker, chat, GitHub reviews). Ask in plain text. When the user says yes, give the step to the implementer in `lead-ops-N.md` with stop conditions:
- pin the reviewed head: `gh pr merge --squash --match-head-commit <sha>`, never `--admin`;
- give the expected plan summary: `terraform plan -out`, then apply that saved plan;
- stop at the first failure;
- report in `ops-N.md`.

The implementer runs these steps because an isolated lead cannot run git in other checkouts (Gotchas). A test page starts an escalation clock. Send it only when the person who must acknowledge it is at the screen, and give them the deadline at once.

**A PR that must not close a multi-PR ticket:** Linear links a ticket id in a branch name, title or body as "closes". Keep the id out of all three. Then link the PR by hand: GraphQL `attachmentLinkGitHubPR(issueId, url, linkKind: contributes)`. After that, check the issue state and `metadata.linkKind`.

## End

Close the worker panes you created (`herdr pane close`); their sessions stay on disk. If the proof needs time (for example a soak week), schedule it with `follow-up-check`. Give the user the result and the open items.

## Gotchas

- **An isolated lead** (started with `--worktree`) cannot run some Bash calls. Its harness refuses a call that puts a runtime value (`$VAR`, `$(…)`) next to `herdr` or `git`, or that pipes into an interpreter. Use literal ids, one plain command per call, and put scripts in files. It also refuses git in another repo's checkout, so the implementer runs those steps.
- **Codex started through its app-server daemon** runs shell commands in the daemon's environment, so pane `--env` variables are missing. Briefs must carry literal paths and names.
- **`herdr pane move`** stops every open `agent wait` on that agent (`agent_not_running`). Start the watchdogs again after a move.
- **A slash command** sent to a busy Claude pane arrives as plain text. Send `/rename` only when the pane is idle. To rename yourself, run this in the background: `herdr agent wait <t>-lead --until idle --until done && herdr agent prompt <t>-lead "/rename <t>-lead"`.
- **Read files, not panes.** `agent read` shows stale lines when a Codex pane is scrolled.
- **Phone pings:** PushNotification reaches the phone only if mobile push is on in `/config`. Check this at setup. Without it, `log.md` and the chats are the record.
