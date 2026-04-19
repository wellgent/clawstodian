#!/usr/bin/env python3
"""
migrate-session-ledger.py - one-off ledger migration from v0.4.0 to v0.4.1 shape.

v0.4.0 stored every session the sessions-capture routine observed in
memory/session-ledger.md, including ones with `classification: skipped`
(cron, hook, sub-agent, dreaming, delivery-only).

v0.4.1 keeps interactive sessions only; skipped classes are re-derived on
every scan by scripts/scan-sessions.py and never written.

This script migrates an existing ledger to the v0.4.1 shape:

1. Drops every H2 block whose body contains `- classification: skipped`.
2. Strips the now-redundant `- classification: interactive` field line from
   the entries that remain (their classification is implicit - if they are
   in the ledger, they are interactive).

Idempotent: running it on an already-migrated ledger is a no-op and exits
with a clear "no changes" message.

Usage (from the workspace root):

    clawstodian/scripts/migrate-session-ledger.py              # apply in place
    clawstodian/scripts/migrate-session-ledger.py --dry-run    # preview to /tmp/
    clawstodian/scripts/migrate-session-ledger.py --path <p>   # migrate a different file

Prints a one-line summary to stderr. Writes atomically via a temp file in
the same directory so a partial write can't leave a corrupted ledger.

Exit codes: 0 success, 2 input path missing.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path


HEADING_RE = re.compile(
    r"^(## [0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\s*\n)",
    re.MULTILINE | re.IGNORECASE,
)
SKIPPED_RE = re.compile(r"^- classification:\s*skipped\s*$", re.MULTILINE)
INTERACTIVE_FIELD_RE = re.compile(r"^- classification:\s*interactive\s*\n", re.MULTILINE)


def migrate(src: str) -> tuple[str, dict[str, int]]:
    """Return (migrated_text, counts)."""
    counts = {
        "entries_total": 0,
        "entries_dropped_skipped": 0,
        "entries_kept_interactive": 0,
        "classification_lines_stripped": 0,
    }
    # Split on H2 headings, preserving each heading as its own token so we can
    # reattach it to its body when emitting.
    parts = HEADING_RE.split(src)
    preamble = parts[0]
    out: list[str] = [preamble]
    for heading, body in zip(parts[1::2], parts[2::2]):
        counts["entries_total"] += 1
        if SKIPPED_RE.search(body):
            counts["entries_dropped_skipped"] += 1
            continue
        new_body, n_stripped = INTERACTIVE_FIELD_RE.subn("", body)
        counts["classification_lines_stripped"] += n_stripped
        counts["entries_kept_interactive"] += 1
        out.append(heading + new_body)
    return "".join(out), counts


def atomic_write(target: Path, content: str) -> None:
    """Write content to target atomically via a temp file in the same directory."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=target.parent,
        prefix=target.name + ".",
        suffix=".tmp",
    ) as f:
        f.write(content)
        tmp_path = Path(f.name)
    os.replace(tmp_path, target)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Migrate memory/session-ledger.md from v0.4.0 to v0.4.1 shape."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration to /tmp/session-ledger-migrated.md without modifying the workspace file.",
    )
    parser.add_argument(
        "--path",
        default="memory/session-ledger.md",
        help="Ledger file to migrate (default: memory/session-ledger.md).",
    )
    args = parser.parse_args(argv)

    ledger = Path(args.path)
    if not ledger.exists():
        print(f"migrate-session-ledger: {ledger} does not exist", file=sys.stderr)
        return 2

    src = ledger.read_text(encoding="utf-8")
    migrated, counts = migrate(src)

    summary = (
        f"migrate-session-ledger: entries={counts['entries_total']} "
        f"dropped_skipped={counts['entries_dropped_skipped']} "
        f"kept_interactive={counts['entries_kept_interactive']} "
        f"classification_lines_stripped={counts['classification_lines_stripped']}"
    )

    if args.dry_run:
        tmp = Path("/tmp/session-ledger-migrated.md")
        tmp.write_text(migrated, encoding="utf-8")
        print(f"{summary} (dry run - wrote preview to {tmp})", file=sys.stderr)
        return 0

    if src == migrated:
        print(f"{summary} (no changes - ledger already in v0.4.1 shape)", file=sys.stderr)
        return 0

    atomic_write(ledger, migrated)
    print(summary, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
