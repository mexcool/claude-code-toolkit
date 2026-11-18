# Parent: a session that runs several loops

Read this only if you start several `ticket-orchestrator` leads and stand between them and the user. The lead's side is "When a parent started you" in [SKILL.md](SKILL.md).

**Role.** You do not lead a ticket. You triage, write tickets and briefs, start leads on the user's word, watch their reports, relay decisions, read each change yourself before a merge question, and keep the parent ticket current.

## Setup

One folder for the group, `~/ticket-orchestrator/<PARENT>-meta/`:

- `log.md`: one line for each event, time from `date -u`.
- `inbox.md`: the leads append to it.
- `brief-<id>.md` and `answer-<id>-<n>.md` for each lead.
- `scripts/` and `evidence/`. Keep scripts here, not in a temporary folder: that folder can be deleted.

## Before a start

- Check the usage limits (`claude-limits`). Measure what the first loop uses in an hour before you start more. Do not start into paid overage without the user's word.
- Check that the ticket is true today: read the code it names on a fresh `origin/main`. Write the corrections as a comment on the ticket and in the brief.

## The brief

One file for each lead; it is the lead's only context, so state what you already ruled out. Sections:

1. Who the parent is and how to report.
2. Read first: the ticket, code paths, evidence, the last PR of the same kind.
3. Facts the ticket does not have.
4. Rules: one change; what must not change; the proof and the run budget; overlaps with other open PRs and running loops, by file.
5. PR text rules.
6. The report channel: the inbox file, or `hc send <parent>` under the herdr app.

## Starting a lead

The lead needs its own worktree (`claude --worktree`). Start it with a name, then send `/ticket-orchestrator PROJ-123. Brief from the parent: <path>` (the slash command may carry a plugin prefix).

| Multiplexer | Start |
|---|---|
| herdr | `herdr tab create --cwd <repo> --label <t>-lead`; in its pane, run the launch command with `herdr pane run`; wait until `herdr agent get` shows the agent ready; `herdr agent rename`; then `herdr agent prompt <t>-lead "<command>"`. |
| Rex | A new session that runs the launch command (the Rex guide has the flags); then `rex send` the slash command and `rex send-key enter`. |
| herdr app | `hc run --bg --outlive-parent --name <t>-lead --cwd <repo> claude --dangerously-skip-permissions --worktree -n <t>-lead "/ticket-orchestrator PROJ-123. Brief from the parent: <path>"` |

`hc run` does not expand shell aliases, so spell out the flags. `--outlive-parent` keeps the lead when your program ends. `scripts/mux.sh` already has `start`, `prompt`, `wait` and `read` for the three: reuse them for the lead's pane instead of copying their calls.

## Answers

Write each answer as a file and send one line with its path. Quote the user's words. State:

- **Authorized:** the exact command, with the head pinned.
- **Not authorized.**
- **Conditions and stops:** a conflict, a queue drop or a reviewer's change request means stop and report. Do not retry.
- **What to report after.**

## A new finding from a lead

Triage it yourself; do not ask the user item by item.

- A real defect, a real improvement, or a leverage item with a clear task gets a ticket at once.
- A nit, an item with no measured effect, or one with no clear task gets one line under "Found later" on the parent ticket.
- Search the tracker before you file. Measure before you file when one cheap run or one query gives the rate.

## Before each merge question to the user

The lead's and the reviewers' approval do not replace this.

- Read the diff yourself against the contract. For a later head, read the change since your last read.
- Read the run results yourself, against the history of each failed item, not against what was expected. A count taken from retry attempts is biased toward failures; use a sampled run for a rate.
- Check `mergeable` again, and the PRs that merged the same day: a stricter shared rule in one PR can break a new fixture in another, and CI on each branch does not show it.
- Check who approved and on which commit. A push dismisses an approval, so the last push comes before the review request, and the review request goes out one time.
- Say first what the change improves for the user and what it does not move, then the rules that failed, then the question. Give a recommendation.

## Relaying

An approval in one context does not extend to the next: a merge yes is for the head and content that the user saw. A review request, or a message to a person outside the PR, needs the user's word.

## Keeping state

After each event: the log line, the parent ticket (edit one exact text, do not rewrite the whole description), and the ticket states. A lead's merge can move the parent ticket's state; check it.

## What exists already

Use the existing tool when it fits. Use a script (in `scripts/`; each prints its usage with `--help`) only where it adds something.

| Script | Does | Exists already |
|---|---|---|
| `inbox-watch.sh <file> [state-file]` | Blocks until the file has new lines, prints them, and stores its position in a state file (default `<file>.seen`), so the caller passes no line count. | Under the herdr app a child reports with `hc send` and the parent waits with `hc wait --children`; use that when each lead is a child. The file is the durable record in each case. |
| `wait-until.sh <HH:MM>` | Waits until that UTC time. | A scheduler or a wakeup tool of the harness, when there is one. |
| `wait-runs.sh <owner/repo> <run-id>...` | Waits until each CI run is complete and prints status and conclusion. | `gh run watch <id>` for one run. |
| `wait-scheduled-run.sh <owner/repo> <workflow> <after-iso-time>` | Waits for the next scheduled run of a workflow that was created after the time, and prints its id and conclusion. | Nothing equal in `gh`. |
| `ticket-edit.py <ID> --replace-file <old.txt> <new.txt> [--apply]` | Replaces one exact text in a ticket description; stops when the text is not there exactly one time; dry run by default. | The Linear connector's `save_issue` with `patch`, when the session has it. Use the script when only the command line tool is there. |

## Pitfalls

Each one happened.

- An inbox watch restarted with a wrong line count nearly missed a line. Use a watch that keeps its own position (`inbox-watch.sh`).
- A background command started with `&`, or with its output discarded, loses its result. Use the harness's background mode and read its output file.
- Moving the session to another terminal stops its background tasks. Write a resume note in the log first: what to start again, with which arguments.
- The input box of an idle agent pane can show a suggested prompt, and a bare Enter submits it. Type the text, read the pane, then send Enter.
- Leads write times from memory. Trust the times of the tracker and of the code host.
- Sessions of one project can share one memory folder; expect edits from the leads.
