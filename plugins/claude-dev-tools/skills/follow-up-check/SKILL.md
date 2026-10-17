---
name: follow-up-check
description: "Schedule a later check on work that already shipped but cannot be verified yet (no traffic since the deploy, a 7-day window, a metric that needs time): a Linear comment now with the check plan in a gist, and a native Linear reminder that pings the user on the due date. Use when asked to schedule a post-deploy or post-merge check, or to be reminded on a ticket to verify a change later."
version: 0.2.0
---

# Follow-up check

A change shipped, but its proof needs data that does not exist yet. Hand the check to a future session: a self-contained plan in a gist, a ticket comment that links it, and a reminder that pings the user on the due date.

The session that runs the check starts cold. **Capture now what only this session knows**: what shipped, the baseline numbers, the method, and the pass rule.

## Steps

1. **Measure the baseline now**, with the script the check will run later. A before/after comparison is only valid when both sides use one method. Use a "before" window that ends at the deploy.
2. **Make the scripts survive until the due date:** take the time window as arguments; default to a checkout that will not be deleted (not a worktree) and allow an env var override; fail loudly when a query hits a row cap; print a clear line when the window holds no data.
3. **Write `FOLLOWUP.md`** (template below) and put it in a secret gist with the scripts (see the `gist` skill). A fresh session must be able to run the check from it alone. The gist is the living plan: correct it there, not in the comment.
4. **Get the due date and the session facts:**

   ```bash
   S=<this-skill-dir>/scripts/follow-up.py
   uv run $S due --days 14     # next weekday 08:30 UTC; --at HH:MM, --weekend
   uv run $S session           # id, start cwd, resume command, claude.ai link
   ```

5. **Post the follow-up comment on the Linear issue now** (template below), with the Linear MCP `save_comment`.
6. **Set a Linear reminder for the due time** and verify it (next section). This is the ping.
7. **Report** to the user: the comment, the reminder time, the gist link. Save it to memory if the project keeps one.

**Optional — a dated comment.** If people who follow the issue should see a new comment on the due date, also create a one-shot cloud routine with the `/schedule` skill: `run_once_at` from `due`, the cheapest capable model, no repository write tools, only the Linear connector. Put the comment text in the prompt after "Post this text exactly. Do nothing else: no code changes, no other comments, no status change. If you cannot find the issue or cannot post, stop and report why." A cloud agent asked to compose a comment improvises. The routine posts through the user's own connector, so it may not ping the user; keep the reminder.

## The reminder

Linear's `issueReminder` mutation puts a snoozed notification in the inbox of whoever sets it. The Linear MCP has no tool for it, so use any authenticated GraphQL client: a personal API key (`LINEAR_API_KEY`) with `curl`, or a Linear CLI that can send GraphQL. If neither exists, set it by hand with **Remind me** on the issue in the Linear app.

```bash
curl -s https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" -H 'Content-Type: application/json' \
  -d '{"query":"mutation { issueReminder(id: \"PROJ-123\", reminderAt: \"2026-01-05T08:30:00Z\") { success } }"}'
```

`success: true` alone does not prove the reminder exists, so verify: the inbox must hold a notification of `type: "issueReminder"` for the issue, with `snoozedUntilAt` at the due time. The Linear MCP `get_notifications` hides snoozed notifications, so use GraphQL:

```graphql
{ notifications(first: 10) { nodes { type snoozedUntilAt ... on IssueNotification { issue { identifier } } } } }
```

A reminder reaches only the channels the user enabled in Linear (inbox, desktop, mobile, email, Slack). Read them with `{ userSettings { notificationChannelPreferences { desktop mobile email slack } } }` and tell the user where it will arrive. For a Slack ping too, the user turns on Linear's Slack delivery or types a `/remind` line you give them. A message an agent posts as the user is the user's own message: Slack does not notify anyone of their own messages, and Linear may not either.

## `FOLLOWUP.md` template

```markdown
# PROJ-123 follow-up check (due YYYY-MM-DD)

**Ask:** <the question the check answers, and any reviewer question it also answers>.

## Facts
- What shipped: PR, merge commit, deploy time, the version or image that runs it.
- What was verified at ship time, what was not, and why.
- The baseline: numbers, window, and the command that produced them.

## Checks
Numbered, each with the exact command (window = deploy time to $NOW) and a pass rule:
which value must hold, and which exceptions are expected (a known fallback path).
The last check is "post the result on the issue; if it fails, reopen with examples".

## Original session (only for the reasoning behind a decision)
cd <start cwd> && claude --resume <session id>
```

Start the check in a fresh session from `FOLLOWUP.md`. Resume the original session only to read why something was decided: a resumed session reloads all of its context, and part of it is out of date by then.

## Comment template

```text
**Follow-up check due YYYY-MM-DD.** <one sentence: what shipped and when>.
<one sentence: why it cannot be verified yet>.

Checks: 1. <check> 2. <check> …
Run from: <where the data is reachable, for example a local session with VPN access>
Plan, commands, scripts and baselines: `FOLLOWUP.md` in <gist url>
Original session: `cd <start cwd> && claude --resume <session id>`
```

## Pitfalls

- **Transcripts expire.** Claude Code deletes a transcript after `cleanupPeriodDays` of inactivity (default 30). `due` warns when the due date is close to that; past it, the resume line points at nothing and `FOLLOWUP.md` must carry everything.
- **The check needs private data; the comment does not.** Data behind a VPN or in a cluster is read from a local session, so say in the comment where to run the check.
- **A session resumes from the directory it started in.** If that worktree is deleted, resume from the parent repo. If the id is lost, `agent-sessions find PROJ-123` finds the transcript and prints the command.
- **Put no unverified claim in the comment.** It is read cold. Facts that may still change (baselines, pass rules) belong in the gist, which can be corrected.
- **Do not let the follow-up block the merge.** Ship, then schedule the proof.
