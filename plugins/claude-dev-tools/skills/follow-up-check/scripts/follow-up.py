#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# ///
"""
The two facts a scheduled follow-up check needs from the current session.

  follow-up.py session                 # id, start cwd, resume command, web link
  follow-up.py session --id 9f3c1a2b-… # same, for another session
  follow-up.py due --days 14           # next weekday at 08:30 UTC

`session` reads CLAUDE_CODE_SESSION_ID, which Claude Code sets in every tool
call, instead of guessing from the newest transcript: parallel sessions in one
directory make "newest" wrong. The start cwd comes from the transcript, because
Claude Code keys a session by the directory it started in, not where it is now.

`due` rolls a weekend date forward to Monday: "in two weeks" from a Saturday is
a Saturday, and a ping nobody reads until Monday is a ping lost in the noise.
It warns when the due date is close to `cleanupPeriodDays` (default 30), after
which Claude Code deletes the transcript and the resume command points at
nothing.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import UTC, datetime, time, timedelta
from pathlib import Path

CONFIG = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
PROJECTS = CONFIG / "projects"
# A transcript idle this long is deleted; keep a margin for late resumes.
CLEANUP_DEFAULT_DAYS, CLEANUP_MARGIN_DAYS = 30, 5
# Same override as the agent-sessions skill, for wrapper aliases.
CLAUDE_CMD = os.environ.get("AGENT_SESSIONS_CLAUDE_CMD", "claude")


def find_transcript(session_id: str) -> Path | None:
    hits = sorted(PROJECTS.glob(f"*/{session_id}*.jsonl"))
    return hits[0] if len(hits) == 1 else None


def start_cwd(path: Path) -> str | None:
    """The directory the session resumes from. A `claude --worktree` session records
    the worktree as its cwd but may be filed under the repo root's slug, so walk up
    to the directory whose slug matches the transcript's project dir."""
    with path.open() as fh:
        for _, line in zip(range(200), fh):
            try:
                cwd = json.loads(line).get("cwd")
            except (ValueError, AttributeError):
                continue
            if cwd:
                for p in (Path(cwd), *Path(cwd).parents):
                    if re.sub(r"[^A-Za-z0-9]", "-", str(p)) == path.parent.name:
                        return str(p)
                return cwd
    return None


def cmd_session(args: argparse.Namespace) -> None:
    session_id = args.id or os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not session_id:
        sys.exit("no session id: pass --id, or run this inside Claude Code")
    path = find_transcript(session_id)
    if path is None:
        sys.exit(f"no single transcript matches {session_id} under {PROJECTS}")
    session_id = path.stem
    cwd = start_cwd(path)
    if cwd is None:
        sys.exit(f"no cwd recorded in {path}")

    print(f"session_id: {session_id}")
    print(f"start_cwd:  {cwd}")
    if not Path(cwd).is_dir():
        print("warning:    the start directory is gone; resume from the parent repo")
    print(f"resume:     cd {cwd} && {CLAUDE_CMD} --resume {session_id}")
    # Set when the session is reachable from claude.ai (Remote Control).
    bridge = None if args.id else os.environ.get("CLAUDE_CODE_BRIDGE_SESSION_ID")
    if bridge:
        print(f"web:        https://claude.ai/code/{bridge}")


def cleanup_days() -> int:
    try:
        settings = json.loads((CONFIG / "settings.json").read_text())
        return int(settings.get("cleanupPeriodDays", CLEANUP_DEFAULT_DAYS))
    except (OSError, ValueError, TypeError):
        return CLEANUP_DEFAULT_DAYS


def cmd_due(args: argparse.Namespace) -> None:
    hour, minute = (int(part) for part in args.at.split(":"))
    now = datetime.now(UTC)
    day = (now + timedelta(days=args.days)).date()
    while not args.weekend and day.weekday() >= 5:
        day += timedelta(days=1)
    due = datetime.combine(day, time(hour, minute), tzinfo=UTC)
    print(f"due: {due:%Y-%m-%dT%H:%M:%SZ}  ({due:%A})")
    keep = cleanup_days()
    if (due - now).days > keep - CLEANUP_MARGIN_DAYS:
        print(
            f"warning: transcripts are deleted after {keep} idle days (cleanupPeriodDays); "
            "the resume command may point at nothing, so FOLLOWUP.md must carry everything"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(required=True)

    session = sub.add_parser("session", help="the session to resume when the check is due")
    session.add_argument("--id", help="a session id or prefix (default: this session)")
    session.set_defaults(func=cmd_session)

    due = sub.add_parser("due", help="when the check is due, in UTC")
    due.add_argument("--days", type=int, required=True, help="days from now")
    due.add_argument("--at", default="08:30", help="time of day, HH:MM UTC (default 08:30)")
    due.add_argument("--weekend", action="store_true", help="allow a Saturday or Sunday")
    due.set_defaults(func=cmd_due)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
