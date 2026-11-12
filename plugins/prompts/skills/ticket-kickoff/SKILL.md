---
name: ticket-kickoff
description: Gather full cross-repo, cross-ticket context before writing any code for a ticket. Use when starting work on a ticket, "tackling" or "doing" a ticket, or whenever the user gives you a ticket ID and expects you to come up to speed before acting.
---

# Ticket Kickoff

The user gave you a ticket (ID or URL). Build a full picture before touching any code.

## Steps

1. **Read the ticket** itself — description, comments, attachments.
2. **Follow every link**: parent, sub-issues, blocked-by, blocks, related, and any tickets mentioned in the body or comments. Read them too. The ticket usually only makes sense as one node in a wider initiative — find that initiative.
3. **Identify the repos involved**. The work may span backend, data, frontend, infra, SDKs. Read the relevant code in each — not just one repo.
4. **Check recent PRs** touching the same area, even merged ones. Patterns and conventions live there.
5. **Go to the raw evidence**: reproduce the problem or measure the current state from the data, logs or a real run, not from the ticket's summary or the schema. The ticket's diagnosis is a claim to check. If you can't reach the source, say what access is missing.
6. **Summarize in the chat**, before writing any code:
   - The outcome behind the ticket (the wider initiative it fits into), and whether the ticket's route is the simplest way there. Propose a different route as a question.
   - Current state of the system, with the evidence from step 5.
   - What needs to happen, in what order. If the change touches load, money, paging, numbers people decide on or outside input, plan that field's standard check.
   - How we'll know it works: a check per "Done when" item, run through the real dependency, not a mock that skips the behaviour at risk. Back each accepted risk with a measurement run before merge, on main and on the branch, not an argument or a post-merge watch.
   - Anything ambiguous or under-specified — ask about it rather than guessing.
