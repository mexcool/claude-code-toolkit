---
name: kickoff-review
description: Review a ticket kickoff or implementation plan written by another agent, before any code is written. Use when the user pastes a kickoff and asks you to review it ("review the kickoff below for a ticket", "what do you think of this kickoff/plan").
---

# Kickoff Review

The user pasted a kickoff for a ticket, written by another agent. Review it before any code is written. Read the ticket (Linear MCP) and the code yourself; don't just trust the paste. Main moves fast: fetch, review against the latest `origin/main`, and say which commit.

- Focus on simplicity: the simplest plan that does what the ticket needs. Flag scope creep and overengineering, including in your own suggestions.
- Check the board and open PRs: does anything need to land first, or will something collide?
- If the kickoff reinterprets the ticket, check that against what the product does, not only what the code allows.
- You review; the other agent implements. Don't edit code or touch tickets or PRs.

"Looks good, go" is a valid answer.

## Later rounds

The user will relay the other agent's replies, and later its PR.

- On a reply, recheck only the disputed points. Concede when they're right; hold with evidence when they're not. Don't open new fronts without new information.
- On the PR, also check it against the plan you agreed: anything agreed but missing, anything built that wasn't.
- On fix commits, check your earlier findings and look for regressions. If the fixes are broad (new files, a changed approach), do a full pass.
