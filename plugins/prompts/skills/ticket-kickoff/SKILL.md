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
5. **STOP. Do not write code yet.**
6. **Summarize in the chat**:
   - What the ticket is asking for and why (the wider initiative it fits into).
   - Current state of the system relative to that ask.
   - What needs to happen, in what order.
   - Anything ambiguous or under-specified.
7. **Ask clarifying questions** before proceeding. If scope is clear, propose a plan and wait for the user's go-ahead.
