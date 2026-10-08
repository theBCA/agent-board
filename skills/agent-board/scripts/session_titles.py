#!/usr/bin/env python3
"""Print the running Claude Code sessions with their tab titles, as JSON.

Each row: {"name", "session_id", "cwd", "status", "title"}.

The name is what SendMessage addresses (e.g. "myrepo-b5"); the title is what the
person sees on the session's tab. Claude Code keeps the title in the session's
transcript: a "custom-title" entry when the person renamed the session, else
the latest "ai-title" entry. A session with neither gets title null.

Usage: python3 session_titles.py [--cwd DIR]
"""

import argparse
import json
import pathlib
import subprocess
import sys

PROJECTS = pathlib.Path.home() / ".claude" / "projects"


def running_sessions(cwd):
    cmd = ["claude", "agents", "--json"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=cwd).stdout
        rows = json.loads(out or "[]")
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        sys.exit(f"could not list sessions with `{' '.join(cmd)}`: {exc}")
    return rows if isinstance(rows, list) else []


def transcript(session_id):
    hits = sorted(PROJECTS.glob(f"*/{session_id}.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[0] if hits else None


def title_of(session_id):
    path = transcript(session_id)
    if not path:
        return None
    custom = ai = None
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if '"custom-title"' not in line and '"ai-title"' not in line:
                continue
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if entry.get("type") == "custom-title":
                custom = entry.get("customTitle") or entry.get("title") or custom
            elif entry.get("type") == "ai-title":
                ai = entry.get("aiTitle") or ai
    return custom or ai


def main():
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--cwd", help="only sessions whose working directory is this path")
    args = ap.parse_args()
    rows = []
    for s in running_sessions(args.cwd):
        if args.cwd and pathlib.Path(s.get("cwd", "")).resolve() != pathlib.Path(args.cwd).resolve():
            continue
        sid = s.get("sessionId")
        rows.append({
            "name": s.get("name"),
            "session_id": sid,
            "cwd": s.get("cwd"),
            "status": s.get("status"),
            "title": title_of(sid) if sid else None,
        })
    json.dump(rows, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
