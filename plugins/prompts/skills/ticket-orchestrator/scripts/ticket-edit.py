#!/usr/bin/env python3
"""ticket-edit.py <ID> --replace-file <old.txt> <new.txt> [--apply]

Replaces one exact text in a ticket description. The text of <old.txt> must occur exactly once in
the description, or nothing changes. Dry run unless --apply is given. Needs `linear-cli`.

Exists already: the Linear connector's `save_issue` with `patch`, when the session has it.
Use this script when only the command line tool is there.
"""
import json
import subprocess
import sys

args = sys.argv[1:]
if len(args) < 4 or args[1] != "--replace-file" or set(args[4:]) - {"--apply"}:
    sys.exit(__doc__)
ticket, old_path, new_path = args[0], args[2], args[3]
old, new = open(old_path).read(), open(new_path).read()

raw = subprocess.run(
    ["linear-cli", "-o", "json", "issues", "get", ticket, "--fields", "description", "--compact"],
    capture_output=True, text=True, check=True,
).stdout
text = json.loads(raw)["description"]
if text.count(old) != 1:
    sys.exit(f"expected exactly one match of {old_path}, found {text.count(old)}")
text = text.replace(old, new)
if "--apply" in args:
    subprocess.run(["linear-cli", "issues", "update", ticket, "-d", text, "-q"], check=True)
    print(f"{ticket} updated")
else:
    print("the text matches once; dry run, pass --apply to write")
