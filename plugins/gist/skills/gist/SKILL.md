---
name: gist
description: >
  Use when creating, sharing, reading, or consuming GitHub Gists as pastebin snippets.
  Triggers on: sharing code/queries/configs, creating gists, reading gist URLs, piping gist content
  to other tools, or when a user pastes a gist URL.
allowed-tools:
  - Bash(gh gist:*)
  - Bash(gh api gists/*)
  - Write
---

**Note:** Reload this skill each turn you need gist tools — permissions don't persist across turns.

# GitHub Gists — Pastebin

Use GitHub Gists as a lightweight pastebin for sharing code snippets, queries, configs, and troubleshooting artifacts.

## When to Use

- SQL queries, code snippets, config samples
- Troubleshooting artifacts, reproduction steps
- Any text artifact worth sharing with a colleague via URL

## When NOT to Use

- Secrets, credentials, API keys, tokens
- Actual query result data — share the **query** instead, not the output
- Logs containing sensitive data (PII, internal IPs, credentials)

## Conventions

- **Always private/secret** (default for `gh gist create`)
- **Descriptive filename with correct extension** — e.g. `repro.sql`, `debug_config.yaml`. GitHub renders syntax highlighting based on extension
- **Concise description** with ticket number if available, e.g. `--desc "TST-123: repro for failing migration"`

## Creating

```
gh gist create --desc "TST-123: description" file.sql
gh gist create --desc "description" file1.sql file2.sql   # multi-file
```

## Reading & Consuming

```
gh gist view <url-or-id> --raw                    # print contents
gh gist view <url-or-id> --raw > output.sql       # save to file
gh gist view <url-or-id> --filename f --raw       # specific file in multi-file gist
```

**Get filename** (not shown by `gh gist view`):
```
gh api gists/<id> --jq '.files | keys[]'
```

**View revisions**:
```
gh api gists/<id> --jq '.history[] | {version, committed_at, change_status}'
```

### Piping to Other Tools

`gh gist view --raw` writes the gist body to stdout, so it composes with any CLI:

- **Direct pipe**: `gh gist view <id> --raw | <consumer>`
- **Save then pass**: redirect to a file (`gh gist view <id> --raw > /tmp/snippet.sql`) when the consumer needs a path, or when you want to inspect/edit before running
- **Multi-file gists**: use `--filename` to select one file at a time
