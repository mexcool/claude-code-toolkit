---
description: Summarize the current session and save it as a note in the Obsidian work vault
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Bash(date *)
  - Bash(printenv OBSIDIAN_WORK_VAULT)
  - Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/get-session-id.py)
---

You are wrapping up a Claude Code session. Your job is to create a session note in the Obsidian work vault.

## Step 0: Load Vault Path and Conventions

1. Run `printenv OBSIDIAN_WORK_VAULT` to get the vault path. If the variable is not set, stop and tell the user to set `OBSIDIAN_WORK_VAULT` in their shell profile.
2. Check if `start-here.md` exists in that vault path using the Read tool. If it exists, follow those conventions exactly. If not, use the defaults in this command.
3. **Get the session ID** — Claude Code does not expose the session ID as an environment variable. Run the helper script:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/get-session-id.py
   ```
   This prints the session's custom title if renamed, or the UUID otherwise. Use the output for the `session-id` frontmatter field.

## What To Do

1. **Generate the filename** using the current date and time: `YYYY-MM-DD-HH-MM-short-description.md` (max 4 words in the description, kebab-case). Pick a description that captures the main thing done in this session.

2. **Build the frontmatter** with these fields:
   - `type: session`
   - `date: YYYY-MM-DD`
   - `repo:` — the GitHub `owner/repo-name` if this session was in a repo (omit if not)
   - `ticket:` — a URL to the relevant issue tracker ticket if one was involved (omit if not)
   - `session-id:` — the current Claude Code session name or ID so it can be resumed with `claude --resume`. Use whatever session identification is available.
   - `tags: [claude-code]` — always include `claude-code`. Add category tags as needed (e.g., `#repo/name`, `#debugging`, `#planning`, `#research`, `#meetings`, `#infrastructure`)

3. **Write the session note** with these sections:

   **## Goal** — What the session set out to accomplish. One or two sentences.

   **## Context** — Branch, starting point, relevant background. Link to previous session notes if this continues earlier work (check the vault with Glob for related notes).

   **## What Was Done** — Bullet list of concrete changes: PRs, commits, files modified, commands run, decisions implemented. Be specific.

   **## Key Learnings** — Decisions made and why, gotchas, surprises, patterns worth remembering. Skip this section if nothing notable.

   **## Open Items** — Things that still need follow-up or unresolved questions. If there are actionable human to-dos, also add them to the current week's task note.

4. **Check for related session notes** — Use Glob to look for existing notes in the vault that relate to the same repo or ticket. If found, add `[[links]]` in the Context section.

5. **Update the weekly task note** if there are open items that are human to-dos:
   - The current week's task file is `tasks-YYYY-WXX.md`
   - If it doesn't exist, create it with the frontmatter from the conventions
   - Add new tasks with a link back to this session note

6. **Output** — After writing the note, show the user:
   - The filename created
   - A brief summary of what was captured
   - The session-id for resuming later
   - Any tasks added to the weekly list

## Additional Context From User

$ARGUMENTS
