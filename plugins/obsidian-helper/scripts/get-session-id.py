"""Get the current Claude Code session ID or custom title.

Prints the custom title if the session was renamed, otherwise the UUID.
Used by the /done command to populate the session-id frontmatter field.
"""

import json
import os
import glob

project_dir = os.path.expanduser(
    "~/.claude/projects/" + os.getcwd().replace("/", "-")
)

files = sorted(
    glob.glob(os.path.join(project_dir, "*.jsonl")),
    key=os.path.getmtime,
    reverse=True,
)

if not files:
    print("unknown")
    raise SystemExit()

session_file = files[0]
uuid = os.path.basename(session_file).removesuffix(".jsonl")

custom_title = None
with open(session_file) as f:
    for line in f:
        obj = json.loads(line)
        if obj.get("type") == "custom-title":
            custom_title = obj.get("customTitle")

print(custom_title or uuid)
