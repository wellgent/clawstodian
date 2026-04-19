#!/usr/bin/env python3
"""
scan-sessions.py - Classify current sessions against the workspace ledger.

Invokes `openclaw sessions --json`, reads `memory/session-ledger.md`, and emits
the interactive-session queue that `sessions-capture` needs to work. Skipped
sessions (cron, hook, sub-agent, delivery-only) are classified on the fly and
never written to the ledger; they just don't appear in the output.

This is the single authoritative queue for the daily-notes pipeline. Both the
heartbeat orchestrator (to decide whether to enable the burst cron) and the
`sessions-capture` routine (to pick the next target) read from this script.

Invocation (from the workspace root):

    clawstodian/scripts/scan-sessions.py              # full JSON report on stdout
    clawstodian/scripts/scan-sessions.py --next       # single oldest-first target, or exit 1 if empty
    clawstodian/scripts/scan-sessions.py --verbose    # full report + per-session detail on stderr

Output (default) - JSON on stdout:

    {
      "counts": {
        "total_rows": <N>,
        "unique_sessions": <N>,
        "interactive": <N>,
        "skipped_cron": <N>,
        "skipped_hook": <N>,
        "skipped_subagent": <N>,
        "skipped_dreaming": <N>,
        "skipped_empty": <N>,
        "missing_transcript": <N>
      },
      "queue": [
        {
          "session_id": "...",
          "key": "agent:main:...",
          "kind": "direct",
          "transcript_path": "...",
          "updated_at": <ms>,
          "transcript_lines": <N>,
          "lines_captured": <N>,
          "status": "new" | "stale",
          "reason": "..."
        },
        ...
      ],
      "missing_transcripts": [
        { "session_id": "...", "key": "...", "updated_at": <ms> }
      ]
    }

Queue is sorted by updated_at descending (newest first - live sessions capture
before historical drain). Use --next to get just the first entry.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


LEDGER_PATH = Path("memory/session-ledger.md")
DEFAULT_STATE_DIR = Path.home() / ".openclaw"
PEEK_LINES = 200  # how many JSONL lines to scan for a user-role message

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
SESSION_HEADING_RE = re.compile(
    r"^##\s+([0-9a-f-]{36})\s*$", re.IGNORECASE | re.MULTILINE
)
LEDGER_KV_RE = re.compile(r"^- ([a-z_]+):\s*(.*)$")


# ---------------------------------------------------------------------------
# sessions_list ingestion
# ---------------------------------------------------------------------------


def load_sessions_list(path: str | None) -> list[dict[str, Any]]:
    """Load sessions from `openclaw sessions --json` or from a file."""
    if path:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    else:
        try:
            result = subprocess.run(
                ["openclaw", "sessions", "--json"],
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )
        except FileNotFoundError:
            print("scan-sessions: `openclaw` CLI not found on PATH", file=sys.stderr)
            return []
        except subprocess.CalledProcessError as e:
            print(
                f"scan-sessions: `openclaw sessions --json` failed: {e.returncode}",
                file=sys.stderr,
            )
            print(e.stderr, file=sys.stderr)
            return []
        except subprocess.TimeoutExpired:
            print("scan-sessions: `openclaw sessions --json` timed out", file=sys.stderr)
            return []
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"scan-sessions: could not parse openclaw JSON: {e}", file=sys.stderr)
            return []

    rows = data.get("sessions") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        return []
    return rows


def resolve_transcript_path(agent_id: str, session_id: str) -> Path:
    """Resolve the on-disk transcript path per OpenClaw's layout."""
    state_dir_env = os.environ.get("OPENCLAW_STATE_DIR")
    state_dir = Path(state_dir_env).expanduser() if state_dir_env else DEFAULT_STATE_DIR
    return state_dir / "agents" / (agent_id or "default") / "sessions" / f"{session_id}.jsonl"


# ---------------------------------------------------------------------------
# ledger parsing
# ---------------------------------------------------------------------------


def parse_ledger(path: Path) -> dict[str, dict[str, str]]:
    """Parse memory/session-ledger.md into {session_id: {field: value}}."""
    if not path.exists():
        return {}
    entries: dict[str, dict[str, str]] = {}
    current: str | None = None
    with open(path, encoding="utf-8") as f:
        for raw in f:
            heading = SESSION_HEADING_RE.match(raw)
            if heading:
                current = heading.group(1).lower()
                entries[current] = {}
                continue
            if current is None:
                continue
            kv = LEDGER_KV_RE.match(raw.rstrip())
            if kv:
                entries[current][kv.group(1)] = kv.group(2)
    return entries


# ---------------------------------------------------------------------------
# classification
# ---------------------------------------------------------------------------


def classify_by_key(key: str) -> tuple[str, str] | None:
    """
    Early classification based on the session key prefix.

    Returns (bucket, reason) for sessions that are deterministically skipped,
    or None if the session is an interactive candidate that needs transcript
    peek to confirm.
    """
    if ":cron:" in key:
        return ("skipped_cron", "cron session")
    if ":hook:" in key or key.endswith(":hook"):
        return ("skipped_hook", "hook session")
    if ":subagent" in key:
        return ("skipped_subagent", "sub-agent (parent transcript owns content)")
    if ":dreaming-" in key:
        return ("skipped_dreaming", "dreaming routine session")
    return None


# Prefixes that indicate a user-role turn was system-generated, not operator-typed.
# Examples (seen in live transcripts):
#   [cron:866205fb... sessions-capture] Read clawstodian/routines/...
#   [heartbeat:tick] ...
#   [hook:...]
#   System (untrusted): [2026-04-18 21:06:06 UTC] Exec completed (brisk-gu, code 0) ...
#   System: ...
#   Conversation info (untrusted metadata): ...
SYSTEM_USER_PREFIXES = (
    "[cron:",
    "[heartbeat:",
    "[hook:",
    "System (",
    "System:",
    "Conversation info",
)


def has_user_turn(transcript_path: Path, max_lines: int = PEEK_LINES) -> bool:
    """
    Cheap transcript peek: scan the first N JSONL lines for any user-role
    message whose content does NOT match a known system-injection prefix.
    Returns True only on evidence of a real operator turn - this is the
    delivery-only filter from `daily-notes.md`'s classification rules.
    """
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for i, raw in enumerate(f):
                if i >= max_lines:
                    break
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") != "message":
                    continue
                msg = obj.get("message") or {}
                if msg.get("role") != "user":
                    continue
                content = msg.get("content")
                text = ""
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    text = "".join(
                        item.get("text", "")
                        for item in content
                        if isinstance(item, dict) and item.get("type") == "text"
                    )
                text = text.lstrip()
                if text.startswith(SYSTEM_USER_PREFIXES):
                    continue
                if not text:
                    continue
                return True
    except OSError:
        return False
    return False


def count_jsonl_lines(path: Path) -> int:
    """Line count for a transcript file; 0 if missing."""
    try:
        with open(path, "rb") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


# ---------------------------------------------------------------------------
# dedup + scan
# ---------------------------------------------------------------------------


def dedup_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    sessions_list returns one row per (key, sessionId) pair. Multiple keys can
    point to the same transcript (e.g. a cron job's root key + its per-run
    sub-keys). Keep the highest-updatedAt row per sessionId.
    """
    best: dict[str, dict[str, Any]] = {}
    for row in rows:
        sid = (row.get("sessionId") or "").lower()
        if not sid or not UUID_RE.match(sid):
            continue
        incumbent = best.get(sid)
        if incumbent is None:
            best[sid] = row
            continue
        if (row.get("updatedAt") or 0) > (incumbent.get("updatedAt") or 0):
            best[sid] = row
    return list(best.values())


def scan(
    rows: list[dict[str, Any]], ledger: dict[str, dict[str, str]]
) -> dict[str, Any]:
    counts = {
        "total_rows": 0,
        "unique_sessions": 0,
        "interactive": 0,
        "skipped_cron": 0,
        "skipped_hook": 0,
        "skipped_subagent": 0,
        "skipped_dreaming": 0,
        "skipped_empty": 0,
        "missing_transcript": 0,
    }
    queue: list[dict[str, Any]] = []
    missing_transcripts: list[dict[str, Any]] = []
    verbose: list[dict[str, Any]] = []

    counts["total_rows"] = len(rows)
    deduped = dedup_rows(rows)
    counts["unique_sessions"] = len(deduped)

    for row in deduped:
        sid = (row.get("sessionId") or "").lower()
        if not sid:
            continue
        key = row.get("key") or ""
        agent_id = row.get("agentId") or "default"
        updated_at = row.get("updatedAt")
        kind = row.get("kind")

        # Step 1: key-based skip
        early = classify_by_key(key)
        if early is not None:
            counts[early[0]] += 1
            verbose.append({"session_id": sid, "bucket": early[0], "reason": early[1]})
            continue

        # Step 2: transcript check
        transcript_path = resolve_transcript_path(agent_id, sid)
        if not transcript_path.exists():
            counts["missing_transcript"] += 1
            missing_transcripts.append(
                {
                    "session_id": sid,
                    "key": key,
                    "updated_at": updated_at,
                    "transcript_path": str(transcript_path),
                }
            )
            verbose.append(
                {"session_id": sid, "bucket": "missing_transcript", "key": key}
            )
            continue

        # Step 3: empty-transcript skip
        if not has_user_turn(transcript_path):
            counts["skipped_empty"] += 1
            verbose.append(
                {"session_id": sid, "bucket": "skipped_empty", "reason": "no user turns"}
            )
            continue

        # Step 4: interactive. Compare against ledger.
        counts["interactive"] += 1
        transcript_lines = count_jsonl_lines(transcript_path)
        ledger_entry = ledger.get(sid)

        if ledger_entry is None:
            queue.append(
                {
                    "session_id": sid,
                    "key": key,
                    "kind": kind,
                    "transcript_path": str(transcript_path),
                    "updated_at": updated_at,
                    "transcript_lines": transcript_lines,
                    "lines_captured": 0,
                    "status": "new",
                    "reason": "not in ledger",
                }
            )
            continue

        try:
            lines_captured = int(ledger_entry.get("lines_captured", "0") or 0)
        except ValueError:
            lines_captured = 0

        if transcript_lines > lines_captured:
            queue.append(
                {
                    "session_id": sid,
                    "key": key,
                    "kind": kind,
                    "transcript_path": str(transcript_path),
                    "updated_at": updated_at,
                    "transcript_lines": transcript_lines,
                    "lines_captured": lines_captured,
                    "status": "stale",
                    "reason": f"cursor behind ({lines_captured} < {transcript_lines})",
                }
            )
        # else: up-to-date, skip silently

    # Sort queue by updated_at descending (newest first - live sessions before
    # historical drain) with sessionId tie-break for determinism.
    queue.sort(key=lambda e: (-(e.get("updated_at") or 0), e["session_id"]))

    return {
        "counts": counts,
        "queue": queue,
        "missing_transcripts": missing_transcripts,
        "_verbose": verbose,
    }


# ---------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------


def emit_summary_to_stderr(result: dict[str, Any]) -> None:
    c = result["counts"]
    print(
        f"scan-sessions: total={c['total_rows']} unique={c['unique_sessions']} "
        f"interactive={c['interactive']} queue={len(result['queue'])} "
        f"(new={sum(1 for e in result['queue'] if e['status']=='new')} "
        f"stale={sum(1 for e in result['queue'] if e['status']=='stale')}) "
        f"missing_transcript={c['missing_transcript']} "
        f"skipped=cron:{c['skipped_cron']}+hook:{c['skipped_hook']}"
        f"+sub:{c['skipped_subagent']}+dream:{c['skipped_dreaming']}"
        f"+empty:{c['skipped_empty']}",
        file=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify sessions and emit the interactive queue.")
    parser.add_argument(
        "--next",
        dest="next_target",
        action="store_true",
        help="Emit only the single oldest-first pending target; exit 1 if queue is empty.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Emit per-session classification detail on stderr.",
    )
    parser.add_argument(
        "--sessions-json",
        metavar="PATH",
        help="Read sessions list JSON from PATH instead of invoking openclaw.",
    )
    args = parser.parse_args(argv)

    rows = load_sessions_list(args.sessions_json)
    ledger = parse_ledger(LEDGER_PATH)
    result = scan(rows, ledger)

    verbose = result.pop("_verbose")

    if args.next_target:
        if not result["queue"]:
            emit_summary_to_stderr(result)
            return 1
        print(json.dumps(result["queue"][0], indent=None))
        emit_summary_to_stderr(result)
        return 0

    print(json.dumps(result, indent=2))
    emit_summary_to_stderr(result)
    if args.verbose:
        for entry in verbose:
            print(f"  {entry}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
