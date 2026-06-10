#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer>=0.15", "rich>=13"]
# ///
"""
Claude plan usage-limit checker.

Reads the Claude Code OAuth token stored locally and calls the same private
endpoint the `/usage` slash command uses, then prints each usage window
(session, weekly, per-model weekly, monthly extra-usage) with how close it is
to its ceiling.

Why this exists: local log parsers (e.g. ccusage) only know token *cost* — they
estimate limits and are often wrong. This reads the real plan-limit percentages
straight from the source.

Caveats:
- GET /api/oauth/usage is an undocumented, beta-gated endpoint; it can change
  without notice.
- Requires the `user:profile` scope on the token.
- Only applies to subscription auth (Pro/Max/Team). Under Amazon Bedrock or a
  raw API key there are no rolling plan limits — billing is per-token instead.
"""

import json
import os
import platform
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Check Claude plan usage limits (session / weekly / monthly).")
console = Console()

USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
BETA_HEADER = "oauth-2025-04-20"
USER_AGENT = "claude-code/2.1.0"
KEYCHAIN_SERVICE = "Claude Code-credentials"  # macOS Keychain item written by the CLI

# Friendly labels + display order for known windows. Any window the endpoint
# returns that is *not* listed here is still shown, with a prettified label.
WINDOW_LABELS = {
    "five_hour": "Session (5h)",
    "seven_day": "Weekly — all models",
    "seven_day_opus": "Weekly — Opus",
    "seven_day_sonnet": "Weekly — Sonnet",
    "seven_day_oauth_apps": "Weekly — OAuth apps",
}
WINDOW_ORDER = list(WINDOW_LABELS)


def _credentials_paths() -> list[Path]:
    paths = []
    cfg = os.environ.get("CLAUDE_CONFIG_DIR")
    if cfg:
        paths.append(Path(cfg) / ".credentials.json")
    paths.append(Path.home() / ".claude" / ".credentials.json")
    return paths


def load_oauth() -> dict:
    """Return the claudeAiOauth object from the credentials file, or macOS Keychain."""
    for path in _credentials_paths():
        if path.is_file():
            data = json.loads(path.read_text())
            return data.get("claudeAiOauth", data)

    # macOS fallback: the CLI may store creds in the login Keychain instead of a file.
    if platform.system() == "Darwin":
        try:
            raw = subprocess.check_output(
                ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            data = json.loads(raw)
            return data.get("claudeAiOauth", data)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            pass

    searched = ", ".join(str(p) for p in _credentials_paths())
    if platform.system() == "Darwin":
        searched += " and the macOS Keychain"
    console.print(
        f"[red]No Claude credentials found.[/red] Looked in {searched}.\n"
        "Log in with the Claude CLI first (subscription auth required)."
    )
    raise typer.Exit(1)


def fetch_usage(token: str) -> dict:
    req = urllib.request.Request(
        USAGE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "anthropic-beta": BETA_HEADER,
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            console.print(
                f"[red]Auth failed ({e.code}).[/red] The token is expired or lacks the "
                "[bold]user:profile[/bold] scope.\n"
                "Run any Claude command (start a `claude` session) to refresh it, then retry.\n"
                "If you authenticate via Bedrock or an API key, plan limits don't apply."
            )
        else:
            console.print(f"[red]HTTP {e.code}[/red]: {e.read().decode(errors='replace')[:500]}")
        raise typer.Exit(1)
    except urllib.error.URLError as e:
        console.print(f"[red]Request failed:[/red] {e.reason}")
        raise typer.Exit(1)


def _bar(pct: float, width: int = 20) -> str:
    pct = max(0.0, min(100.0, float(pct)))
    filled = round(pct / 100 * width)
    color = "red" if pct >= 80 else "yellow" if pct >= 50 else "green"
    return f"[{color}]{'█' * filled}{'░' * (width - filled)}[/{color}] {pct:>5.1f}%"


def _reset_str(iso: Optional[str]) -> str:
    if not iso:
        return "—"
    try:
        when = datetime.fromisoformat(iso)
    except ValueError:
        return iso
    secs = (when - datetime.now(timezone.utc)).total_seconds()
    if secs <= 0:
        rel = "due"
    elif secs < 3600:
        rel = f"in {int(secs // 60)}m"
    elif secs < 86400:
        rel = f"in {secs / 3600:.1f}h"
    else:
        rel = f"in {secs / 86400:.1f}d"
    return f"{when.strftime('%a %d %b %H:%M UTC')} ({rel})"


def _label(key: str) -> str:
    return WINDOW_LABELS.get(key, key.replace("_", " ").capitalize())


def _is_window(value) -> bool:
    return isinstance(value, dict) and "utilization" in value and "resets_at" in value


def render(data: dict, oauth: dict) -> None:
    plan = oauth.get("subscriptionType") or "?"
    tier = oauth.get("rateLimitTier") or "?"
    console.print(f"\n[bold]Claude usage limits[/bold]  ·  plan: {plan}  ·  tier: {tier}")
    console.print("─" * 64)

    # Collect every window-shaped, non-null entry. Known keys first (in order),
    # then any others the endpoint added that we don't have a label for yet.
    windows = {k: v for k, v in data.items() if k != "extra_usage" and _is_window(v)}
    ordered = [k for k in WINDOW_ORDER if k in windows]
    ordered += sorted(k for k in windows if k not in WINDOW_ORDER)

    if ordered:
        table = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
        table.add_column("Window")
        table.add_column("Utilization")
        table.add_column("Resets")
        for key in ordered:
            w = windows[key]
            table.add_row(_label(key), _bar(w["utilization"]), _reset_str(w.get("resets_at")))
        console.print(table)
    else:
        console.print("[dim]No active rolling windows reported.[/dim]")

    extra = data.get("extra_usage")
    if isinstance(extra, dict) and extra.get("is_enabled"):
        used = extra.get("used_credits", 0)
        limit = extra.get("monthly_limit", 0)
        pct = extra.get("utilization", 0)
        cur = extra.get("currency", "USD")
        # Amounts are reported as integer minor units (cents); render as currency.
        console.print(
            f"\n[bold]Monthly extra-usage[/bold]  {_bar(pct)}"
            f"   {used / 100:,.2f} / {limit / 100:,.2f} {cur}"
        )
        if extra.get("disabled_reason"):
            console.print(f"  [yellow]disabled_reason:[/yellow] {extra['disabled_reason']}")
    console.print()


@app.command()
def main(
    as_json: bool = typer.Option(False, "--json", help="Print the raw endpoint response as JSON."),
) -> None:
    oauth = load_oauth()
    token = oauth.get("accessToken")
    if not token:
        console.print("[red]No accessToken in credentials.[/red]")
        raise typer.Exit(1)
    data = fetch_usage(token)
    if as_json:
        json.dump(data, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        render(data, oauth)


if __name__ == "__main__":
    app()
