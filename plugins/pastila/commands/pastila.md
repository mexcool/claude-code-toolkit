---
description: Create encrypted pastila.nl links from text, files, or AI-generated content
allowed-tools:
  - Read
  - Bash(/usr/bin/python3 -m pip install --user requests cryptography)
  - Bash(/usr/bin/python3 -c "import requests, cryptography")
  - Bash(/usr/bin/python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pastila.py *)
---

Upload content to pastila.nl and get an encrypted, shareable URL. Content is end-to-end encrypted using AES - only someone with the full URL (including the key after #) can decrypt it.

IMPORTANT: You MUST NEVER upload secrets, credentials, API keys, tokens, passwords, private keys, .env files, or any other sensitive information to pastila — even though it uses end-to-end encryption. This is a hard rule with no exceptions. If the user asks you to paste sensitive content, refuse and explain why. Content uploaded to pastila is stored on a third-party server and the encrypted URL could be shared or leaked.

## Prerequisites

Before uploading, check if dependencies are installed:

```bash
/usr/bin/python3 -c "import requests, cryptography"
```

If this fails, install them:

```bash
/usr/bin/python3 -m pip install --user requests cryptography
```

Then proceed with the upload.

## Arguments

`$ARGUMENTS`

## Modes

The script automatically detects the input type:

### Mode 1: Direct Text

**Trigger:** Arguments are plain text (not a file path or URL)

Examples:
- `/pastila "SELECT * FROM users WHERE active = true"`
- `/pastila some inline text here`

### Mode 2: File Input

**Trigger:** Argument is a valid file path

Examples:
- `/pastila ./query.sql`
- `/pastila /path/to/my/document.md`

The script reads the file directly - no need to cat or pipe.

### Mode 3: Conversation/Context

**Trigger:** Arguments ask for conversation, context, or summary to be shared

Examples:
- `/pastila this conversation`
- `/pastila our discussion about the database schema`

For this mode, compose the content first, then pass it as text or save to a temp file.

### Mode 4: Decrypt/Fetch

**Trigger:** Argument is a pastila.nl URL

Examples:
- `/pastila https://pastila.nl/?cafebabe/abc123#key`

---

## Execution

The script handles all modes with a single command pattern:

```bash
/usr/bin/python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pastila.py <argument>
```

Where `<argument>` can be:
- A file path → reads and uploads the file
- A pastila URL → decrypts and outputs content
- Plain text → uploads the text directly

---

## Output

After successful upload:

```
https://pastila.nl/?cafebabe/abc123...#base64key...
```

The URL is end-to-end encrypted. The decryption key is the part after `#`.

---

## Examples

```
/pastila "SELECT * FROM transactions WHERE amount > 1000"
# Uploads the SQL query, returns encrypted URL

/pastila ./reports/monthly-summary.md
# Uploads the markdown file content

/pastila https://pastila.nl/?cafebabe/abc123#base64key
# Fetches and decrypts the content from the URL
```
