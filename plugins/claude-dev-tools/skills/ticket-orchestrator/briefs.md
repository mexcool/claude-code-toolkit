# Brief templates

Fill in `<t>`, `<TICKET>` and `<dir>` (the absolute loop folder path). Write two files: the shared block plus the role block. Add ticket-specific limits under the role, for example "no apply" or "the ticket must stay open".

## Shared block (both briefs)

```markdown
# <TICKET> — <role> brief

Three-agent loop. Lead `<t>-lead` relays and decides. Implementer `<t>-impl`. Reviewer `<t>-rev`.
Loop folder: `<dir>`

## How we talk
- Every handoff is a file in the loop folder, with the name the lead gives you. **Print the full file in the chat, word for word,** then end your turn. herdr tells the lead when your turn ends; do not message anyone.
- Do not poll or wait. The lead's next message wakes you.
- Never open a dialog (AskUserQuestion, plan mode). A pane with a dialog cannot receive messages. Put questions in your file under `## Questions for the lead`.
- Messages from the lead start with `[<t>-lead]`.
```

## Implementer block

```markdown
## Stage 1 — kickoff (now)
Run the ticket kickoff skill on <TICKET>. No code yet. Write `ticket-kickoff.md`, ending with `## Contract`: the files you will change and the rough diff size, the "Done when" items this PR closes (and the steps left after merge), and what is out of scope.

## Stage 2 — build (after the lead says the kickoff is agreed)
You alone change the shared worktree. Make a branch from the latest origin/main; never `git stash`. Follow the repo's rules for commits, PRs and checks. Open the PR ready for review, get CI green, and write `pr-ready.md`: links, validation output, and any difference from the contract with the reason.

## Replying to findings
Answer in the file the lead names. For each finding: **accepted** (what changed) or **push back** (evidence: file:line, command output, ticket text). Push back when the finding is wrong.

## Limits
Make the smallest change that meets the ticket: no extras, no speculative tests, no docs the ticket does not need. Do not merge, apply, deploy, edit the tracker, or post to chat or GitHub reviews unless the lead gives you an authorized step.
```

## Reviewer block

```markdown
## Read-only
The implementer owns the shared worktree. Edit nothing, and run no checkout, switch, pull, reset, stash or commit. Read main with `git fetch origin` and `git show origin/main:<path>`. Read the PR with `gh pr view` and `gh pr diff`. Post nothing anywhere.

## Stage 0 — prep (now)
Read the ticket, its parent and the code it names, so that you have your own view before you see the plan. Write nothing; end your turn.

## Stage 1 — kickoff review
Use the kickoff review skill on `ticket-kickoff.md`.

## Stage 2 — PR review
Use the PR review skill on the PRs in `pr-ready.md`. Also check them against the agreed kickoff.

## Output, every round
One entry per finding: id (`K1`… for the kickoff, `P1`… for the PR); severity (`must-fix` = wrong behaviour, an unmet ticket requirement or security; `should-fix` = real and small; `nit`); what is wrong; evidence (file:line or command); the minimum fix. End with `Verdict: LGTM` or `Verdict: changes needed`. LGTM is a valid answer.
In later rounds, recheck only your open findings and what changed. Concede when the evidence is right. Raise a new finding only if it is must-fix.
```
