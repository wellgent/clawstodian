<!-- template: clawstodian/session-ledger 2026-04-18 -->
# Session ledger

The `daily-notes` program reads and writes this file to keep an idempotent, per-session cursor over OpenClaw's session transcripts. It is the workspace's record of what has already been ingested from each session into the daily notes. The ledger is workspace-owned and git-tracked.

The ledger is NOT a log, and NOT a dashboard for humans. It is a compact authoritative state file that the `capture-sessions` cron reads and updates. Operators rarely need to touch it by hand.

## What the ledger replaces

ops-daily kept `capture-state.json` under its own package tree. clawstodian follows the "workspace is the ledger" principle and stores the same information as a markdown file here, in a form the agent can edit with `Edit` (per-field updates) and `Read` without extra tooling.

## Semantics

Per session, the ledger records whether the session has been classified (interesting vs. filtered out), what portion of its JSONL has been captured into daily notes, which dates that content landed in, and when we last observed it.

- **New un-admitted session** (present in `sessions_list`, absent from the ledger) - `capture-sessions` creates an entry, classifies, reads the transcript from line 0, applies per-date. For dormant sessions (no activity in 7+ days) the entry is marked `status: done`; otherwise `status: active`.
- **Known session with stale cursor** (ledger entry exists but `row.updatedAt > ledger.last_activity`) - `capture-sessions` reads JSONL from `lines_captured` to end, applies per-date, advances the cursor.
- **Session classification says "skip"** (cron, hook, subagent whose parent is already captured, delivery-only) - an entry is still created with `classification: skipped` so the session is not re-examined every tick.

The cursor advances only after the affected daily notes have been written successfully. A partial write leaves the cursor at the old position; the next tick retries from there.

## File shape

```markdown
<!-- template: clawstodian/session-ledger 2026-04-18 -->
# Session ledger

<!-- One H2 section per session, sorted by first_seen ascending. Append new
     sessions to the end. Update cursor fields in place via Edit. Never reorder
     existing sections. The file is read in full by capture-sessions on each
     firing. -->

## 96a0c068-a1b2-c3d4-e5f6-7890abcdef12

- classification: interactive
- kind: main
- first_seen: 2026-04-15T10:00Z
- last_activity: 2026-04-18T14:30Z
- lines_captured: 142
- dates_touched: 2026-04-15, 2026-04-16, 2026-04-17, 2026-04-18
- status: active

## b513d1a5-0000-0000-0000-000000000000

- classification: skipped
- kind: cron
- first_seen: 2026-04-17T06:00Z
- reason: cron session (heartbeat tick)
```

### Fields

- **(heading)** - the full session id as returned by `sessions_list`.
- **classification** - `interactive` (content goes into daily notes) or `skipped` (content is filtered out).
- **kind** - the `kind` field from `sessions_list`: `main` | `group` | `cron` | `hook` | `node` | `other`.
- **first_seen** - ISO-8601 UTC timestamp when the ledger first saw this session.
- **last_activity** - the session's `updatedAt` at the most recent tick that examined it. Mirrors the `sessions_list` row, not derived locally. Used to short-circuit sessions that have not moved since last tick.
- **lines_captured** - the JSONL line offset from the start of the session transcript. Next read starts at line `lines_captured` (0-indexed, so the next unread line is the one at that index). Only set on `classification: interactive` entries.
- **dates_touched** - comma-separated `YYYY-MM-DD` list of the daily notes that have received content from this session. Lets the heartbeat and the operator see at a glance which days the session contributed to. Only set on `classification: interactive` entries.
- **status** - `active` (session still receiving activity) | `dormant` (no activity for 7+ days but transcript still exists) | `done` (fully captured, session closed by gateway). Only set on `classification: interactive` entries.
- **reason** - one short line explaining a `skipped` classification. Only set on `classification: skipped` entries.

## Update rules

- Cursor advances happen via `Edit` with a narrow `old_string` (the exact line) so unrelated fields are never rewritten.
- New sessions are appended at the end of the file as new H2 blocks. Do not insert them in the middle.
- Existing sections are never reordered. The file's chronological shape is the append order, not `first_seen` sort order, so operators can diff the tail to see recent additions.
- The `capture-sessions` routine is the only writer. The heartbeat reads (for gap detection) but does not write.
- If a session's transcript disappears (gateway pruning, operator deletion), leave the ledger entry in place and surface the anomaly in the next run report. Do not delete entries to match observed state.

## Why a flat file and not JSON

The agent reads and writes this file with its normal Read / Edit tools. A structured JSON file would require a helper script to update one field safely; a markdown file with one H2 per session and one `- key: value` per attribute has the same read cost, narrower edits, and is operator-inspectable without tooling.

The tradeoff is size. At 1000 sessions the file approaches 7000 lines, still well within a single Read call. If a workspace ever grows past 10000 sessions, split the ledger by year (`memory/session-ledger-YYYY.md`) rather than switching to a binary format.

## What NOT to put in the ledger

- Full transcript content. That lives on disk in the session JSONL files.
- Summaries of what happened in each session. That lives in the daily notes.
- PARA extraction status. That is the daily note's `para_status` frontmatter field.
- Heartbeat tick records. Those are in `memory/heartbeat-trace.md`.

The ledger is strictly: "what have we processed from which session, and where did it land."

<!-- /template: clawstodian/session-ledger 2026-04-18 -->
