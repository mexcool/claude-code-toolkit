#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer>=0.15"]
# ///
"""
Find, search, and resume Claude Code + Codex agent sessions.

Both CLIs write one JSONL transcript per session. This reads those transcripts,
matches them against live processes, and prints ready-to-paste resume commands.

Transcript layout:
  Claude  ~/.claude/projects/<slugified-start-cwd>/<session-uuid>.jsonl
          subagents nest under <session-uuid>/subagents/agent-<id>.jsonl
  Codex   ~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<session-id>.jsonl

Big transcripts are common (100 MB+), so metadata comes from a bounded head
read and the last user turn from a bounded tail read. Nothing loads whole.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

import typer

app = typer.Typer(
    add_completion=False,
    help="Find, search, and resume Claude Code + Codex agent sessions.",
    no_args_is_help=False,
)

CLAUDE_ROOT = Path.home() / ".claude" / "projects"
CODEX_ROOTS = [
    Path.home() / ".codex" / "sessions",
    Path.home() / ".codex" / "archived_sessions",
]

# Launch commands used in the printed resume lines. Override when the user drives
# these CLIs through wrapper aliases (extra flags, a different auth env, ...).
CLAUDE_CMD = os.environ.get("AGENT_SESSIONS_CLAUDE_CMD", "claude")
CODEX_CMD = os.environ.get("AGENT_SESSIONS_CODEX_CMD", "codex")

HEAD_LINES = 4000  # enough to reach cwd + the first real user turn
TAIL_BYTES = 2_000_000  # enough to reach the last user turn
TICKET_RE = re.compile(r"\b[A-Za-z]{2,5}-\d{1,6}\b")
ARGS_RE = re.compile(r"<command-args>(.*?)</command-args>", re.S)
# rollout-<ISO-ts-with-dashes>-<uuid>.jsonl — anchor on the trailing UUID, never split("-")
UUID_RE = re.compile(
    r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$", re.I
)

# Turns the CLIs inject that are not the user talking.
NOISE_PREFIXES = ("<local-command", "<command-", "<task-notification>", "Caveat:")
NOISE_CONTAINS = (
    "local-command-caveat",
    "<environment_context>",
    "AGENTS.md instructions for",  # Codex injects this as a role=user turn
    "Base directory for this skill:",  # a skill preamble, not the human ask
)


@dataclass
class Session:
    tool: str  # "claude" | "codex"
    sid: str
    path: Path
    mtime: float
    size: int
    cwd: str | None = None
    branch: str | None = None
    first: str | None = None
    last: str | None = None
    args: str | None = None
    tickets: list[str] = field(default_factory=list)
    pid: int | None = None  # set when a live process holds this session

    @property
    def resume_cmd(self) -> str:
        cwd = self.cwd or str(Path.home())
        if self.tool == "claude":
            return f"cd {cwd} && \\\n  {CLAUDE_CMD} --resume {self.sid}"
        return f"cd {cwd} && \\\n  {CODEX_CMD} resume {self.sid}"


def _clean(text: str) -> str:
    return " ".join(text.split())


def _is_noise(text: str) -> bool:
    return text.startswith(NOISE_PREFIXES) or any(n in text[:80] for n in NOISE_CONTAINS)


def _claude_text(rec: dict) -> str:
    msg = rec.get("message")
    if not isinstance(msg, dict):
        return ""
    content = msg.get("content")
    if isinstance(content, list):
        return "".join(
            c.get("text", "")
            for c in content
            if isinstance(c, dict) and c.get("type") == "text"
        )
    return content if isinstance(content, str) else ""


def _codex_text(rec: dict) -> str:
    payload = rec.get("payload") or {}
    if payload.get("role") != "user":
        return ""
    content = payload.get("content")
    if isinstance(content, list):
        return "".join(c.get("text", "") for c in content if isinstance(c, dict))
    return content if isinstance(content, str) else ""


def _iter_json(lines) -> object:
    for line in lines:
        try:
            yield json.loads(line)
        except Exception:
            continue


def _head(path: Path, limit: int = HEAD_LINES) -> list[str]:
    out = []
    with path.open(errors="ignore") as fh:
        for i, line in enumerate(fh):
            if i >= limit:
                break
            out.append(line)
    return out


def _tail(path: Path, nbytes: int = TAIL_BYTES) -> list[str]:
    size = path.stat().st_size
    with path.open("rb") as fh:
        fh.seek(max(0, size - nbytes))
        blob = fh.read()
    return blob.decode("utf-8", "ignore").splitlines()[1:]


def _parse(sess: Session) -> Session:
    text_of = _claude_text if sess.tool == "claude" else _codex_text
    tickets: dict[str, int] = {}

    for rec in _iter_json(_head(sess.path)):
        if sess.tool == "claude":
            sess.cwd = sess.cwd or rec.get("cwd")
            sess.branch = sess.branch or rec.get("gitBranch")
            if rec.get("type") != "user":
                continue
        else:
            payload = rec.get("payload") or {}
            sess.cwd = sess.cwd or payload.get("cwd")
        raw = text_of(rec)
        if not raw:
            continue
        text = _clean(raw)
        if m := ARGS_RE.search(raw):
            sess.args = sess.args or _clean(m.group(1))[:140] or None
        for t in TICKET_RE.findall(text):
            tickets[t] = tickets.get(t, 0) + 1
        if sess.first is None and text and not _is_noise(text):
            sess.first = text[:240]

    for rec in _iter_json(_tail(sess.path)):
        if sess.tool == "claude" and rec.get("type") != "user":
            continue
        text = _clean(text_of(rec))
        if text and not _is_noise(text):
            sess.last = text[:240]

    sess.tickets = sorted(tickets, key=tickets.get, reverse=True)[:4]
    return sess


def _discover(hours: float) -> list[Session]:
    cutoff = time.time() - hours * 3600
    found: list[Session] = []

    for path in CLAUDE_ROOT.glob("*/*.jsonl"):  # one level = top-level sessions only
        st = path.stat()
        if st.st_mtime >= cutoff:
            found.append(
                Session("claude", path.stem, path, st.st_mtime, st.st_size)
            )

    for root in CODEX_ROOTS:
        for path in root.rglob("rollout-*.jsonl"):
            st = path.stat()
            if st.st_mtime < cutoff:
                continue
            if m := UUID_RE.search(path.stem):
                found.append(Session("codex", m.group(1), path, st.st_mtime, st.st_size))

    return sorted(found, key=lambda s: s.mtime, reverse=True)


def _live() -> dict[str, dict]:
    """Map session-id -> {pid, cwd, tool}. Keyed '' for agents with no id on argv."""
    out: dict[str, dict] = {}
    try:
        ps = subprocess.run(
            ["ps", "-eo", "pid=,args="], capture_output=True, text=True, timeout=10
        ).stdout
    except Exception:
        return out
    for line in ps.splitlines():
        line = line.strip()
        if not line:
            continue
        pid_str, _, args = line.partition(" ")
        argv = args.split()
        if not argv:
            continue
        exe = Path(argv[0]).name
        if exe not in ("claude", "codex"):
            continue
        if "app-server" in args or "--serve" in args or "mcp-server" in args:
            continue
        sid = ""
        for i, tok in enumerate(argv):
            if tok in ("--resume", "resume") and i + 1 < len(argv):
                nxt = argv[i + 1]
                if not nxt.startswith("-"):
                    sid = nxt
                break
        pid = int(pid_str)
        try:
            cwd = os.readlink(f"/proc/{pid}/cwd")
        except OSError:
            cwd = None
        out.setdefault(sid, {"pid": pid, "cwd": cwd, "tool": exe})
    return out


def _herdr() -> list[dict]:
    try:
        raw = subprocess.run(
            ["herdr", "agent", "list"], capture_output=True, text=True, timeout=10
        ).stdout
        return json.loads(raw)["result"]["agents"]
    except Exception:
        return []


def _count(path: Path, needle: str) -> int:
    """Stream-count occurrences. Deliberately not shelling out to grep."""
    n, tail = 0, ""
    with path.open("rb") as fh:
        while chunk := fh.read(1 << 20):
            blob = tail + chunk.decode("utf-8", "ignore")
            n += blob.count(needle)
            tail = blob[-len(needle) :] if len(needle) > 1 else ""
    return n


def _age(mtime: float) -> str:
    mins = (time.time() - mtime) / 60
    if mins < 90:
        return f"{mins:.0f}m ago"
    if mins < 60 * 36:
        return f"{mins / 60:.0f}h ago"
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))


def _label(s: Session) -> str:
    """What the session is about. The opening invocation beats a ticket tally —
    transcripts quote unrelated ids (model names, other teams' tickets) freely."""
    if s.args:
        return s.args[:44]
    # A ticket named in the opening turn is the subject; one merely tallied may not be.
    if opening := TICKET_RE.findall(s.first or ""):
        return opening[0].upper()
    if s.tickets:
        return s.tickets[0]
    return (s.first or "?")[:44]


@app.command("list")
def list_sessions(
    hours: float = typer.Option(24, "--hours", "-h", help="Look-back window."),
    repo: str = typer.Option(None, "--repo", help="Substring filter on session cwd."),
    as_json: bool = typer.Option(False, "--json", help="Machine-readable output."),
) -> None:
    """Recent sessions, split into live (reattach) and dead (resume)."""
    live = _live()
    sessions = [_parse(s) for s in _discover(hours)]
    if repo:
        sessions = [s for s in sessions if s.cwd and repo in s.cwd]

    for s in sessions:
        if hit := live.get(s.sid):
            s.pid = hit["pid"]
    # Agents launched without an id on argv (picker, --worktree): match on cwd.
    if anon := live.get(""):
        for s in sessions:
            if s.pid is None and s.cwd and anon.get("cwd") == s.cwd:
                s.pid = anon["pid"]
                break

    if as_json:
        typer.echo(
            json.dumps(
                [
                    {
                        "tool": s.tool,
                        "session": s.sid,
                        "cwd": s.cwd,
                        "branch": s.branch,
                        "tickets": s.tickets,
                        "pid": s.pid,
                        "mtime": s.mtime,
                        "resume": s.resume_cmd.replace("\\\n ", ""),
                    }
                    for s in sessions
                ],
                indent=2,
            )
        )
        return

    agents = _herdr()
    if agents:
        typer.echo("LIVE under herdr — reattach with `herdr`, do NOT resume:\n")
        for a in agents:
            typer.echo(
                f"  {a['agent']:<7} {a['agent_status']:<8} {a['tab_id']:<22} "
                f"{a['terminal_title_stripped']}"
            )
        typer.echo("")

    alive = [s for s in sessions if s.pid]
    dead = [s for s in sessions if not s.pid]

    if alive:
        typer.echo(f"RUNNING ({len(alive)}) — process still up, reattach:\n")
        for s in alive:
            typer.echo(
                f"  [{s.tool}] {_label(s)}  pid {s.pid}  {_age(s.mtime)}\n"
                f"    {s.sid}  ·  {s.cwd}"
            )
        typer.echo("")

    typer.echo(f"RESUMABLE ({len(dead)}) — last {hours:g}h, newest first:\n")
    for s in dead:
        branch = f" [{s.branch}]" if s.branch else ""
        typer.echo(f"  # {_label(s)}{branch} · {_age(s.mtime)} · {s.size / 1e6:.1f} MB")
        if s.last:
            typer.echo(f"  # last: {s.last[:110]}")
        typer.echo(f"  {s.resume_cmd}\n")


@app.command("find")
def find(
    pattern: str = typer.Argument(..., help="Ticket id, PR number, or any string."),
    hours: float = typer.Option(720, "--hours", "-h", help="Look-back window."),
    top: int = typer.Option(8, "--top", help="How many hits to show."),
) -> None:
    """Rank transcripts by how often PATTERN appears. Mention count beats mtime."""
    scored = []
    for s in _discover(hours):
        if n := _count(s.path, pattern):
            scored.append((n, s))
    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        typer.echo(f"No transcript mentions {pattern!r} in the last {hours:g}h.")
        raise typer.Exit(1)

    for n, s in scored[:top]:
        _parse(s)
        typer.echo(
            f"{n:>6}x  [{s.tool}] {s.sid}  {_age(s.mtime)}  {s.size / 1e6:.1f} MB\n"
            f"        cwd: {s.cwd}\n"
            f"        {(s.first or '')[:120]}\n"
            f"  {s.resume_cmd}\n"
        )


@app.command("show")
def show(
    session: str = typer.Argument(..., help="Session id or a unique prefix."),
    limit: int = typer.Option(0, "--limit", "-n", help="Only the last N turns."),
    hours: float = typer.Option(720, "--hours", "-h", help="Look-back window."),
) -> None:
    """Print the human turns of one session — the fast way to read a transcript."""
    matches = [s for s in _discover(hours) if s.sid.startswith(session)]
    if not matches:
        typer.echo(f"No session starts with {session!r} in the last {hours:g}h.")
        raise typer.Exit(1)
    s = _parse(matches[0])
    text_of = _claude_text if s.tool == "claude" else _codex_text

    turns = []
    with s.path.open(errors="ignore") as fh:
        for rec in _iter_json(fh):
            if s.tool == "claude" and rec.get("type") != "user":
                continue
            text = _clean(text_of(rec))
            if text and not _is_noise(text):
                turns.append(text)

    typer.echo(f"# [{s.tool}] {s.sid}\n# cwd: {s.cwd}\n# turns: {len(turns)}\n")
    for t in turns[-limit:] if limit else turns:
        typer.echo(f"- {t}\n")


@app.callback(invoke_without_command=True)
def default(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        ctx.invoke(list_sessions)


if __name__ == "__main__":
    app()
