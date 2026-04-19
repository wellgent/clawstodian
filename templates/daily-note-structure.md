<!-- template: clawstodian/daily-note-structure 2026-04-19 -->
# Daily Note Structure

Single source of truth for the daily-notes pipeline: the daily note's format (frontmatter, structure, what to capture, what sealing does) and the session-ledger format that `sessions-capture` uses as its authoritative capture-state file. In-session agents read this file when appending to today's note; the `sessions-capture`, `daily-seal`, and `para-extract` routines (specs at `clawstodian/routines/`) read it too. Customize per workspace as needed.

Sections:
- [Overview](#overview), [Frontmatter](#frontmatter), [Note Structure](#note-structure), [What to Capture](#what-to-capture), [What Sealing Does](#what-sealing-does) - the daily note model.
- [Session Ledger](#session-ledger) - the capture-state file (`memory/session-ledger.md`) that the `sessions-capture` routine reads and writes.

## Overview

Daily notes live at `memory/YYYY-MM-DD.md`. Each file represents exactly one calendar day.

**The primary writer of daily notes is the agent working in session with the operator.** Per the workspace's memory-maintenance rules, any agent doing notable work appends to today's note as the work happens. That is the default path.

The `sessions-capture` cron is the **backstop**: it catches sessions that did not get fully written up in-session, including sub-agent sessions, cron-kind sessions, gateway-outage gaps, and historical sessions that predate a clawstodian install. Past days are sealed by `daily-seal`. PARA entities get extracted from sealed notes by `para-extract`.

**One canonical file per day.** The primary daily note is always `memory/YYYY-MM-DD.md`. Topic-suffixed variants such as `memory/YYYY-MM-DD-foo.md` may appear during active sessions; the `sessions-capture` routine merges them into the canonical note when it next processes a session touching that date, and `daily-seal` merges them on seal for past dates. Sealed notes never have topic-suffixed siblings.

**Capture state lives in the ledger, not the note.** Per-session cursors (how far each session transcript has been read) live in `memory/session-ledger.md`. Daily notes reference sessions only by id; the `sessions:` frontmatter field is a human-readable attribution list, not capture state.

```
agent in-session (primary)             sessions-capture (burst backstop)        daily-seal (burst)              para-extract (burst)
--------------------------             ---------------------------------        --------------------                --------------------
writes to memory/YYYY-MM-DD.md         picks one session with a gap and         seals one unsealed past-day         propagates sealed note
as work happens; commits;              applies its unread JSONL tail;           note per firing with JSONL          into PARA entities;
pushes                                 prioritizes live over historical         fidelity; status: sealed            flips para_status done
```

## Frontmatter

```yaml
---
date: 2026-04-18
status: active
capture_status: done
para_status: pending
last_updated: 2026-04-18T17:30Z
topics:
  - VPS migration and OpenClaw install
  - 1Password secrets management investigation
people: [Alice, Bob]
projects: [project-a, project-b]
sessions: [96a0c068, b513d1a5]
---
```

### Fields

- `date` - the date this note covers (`YYYY-MM-DD`).
- `status` - `active` while the day is still receiving content, `sealed` after `daily-seal` has finalized it.
- `capture_status` - capture-completeness lifecycle. Unset while capture may still land content (today's note, or past-days where the capture pipeline has not yet demonstrably finished). Set to `done` by the heartbeat when no more content can land here (see "Capture status transitions" below). `daily-seal` reads `status: active` + `capture_status: done` as its queue.
- `para_status` - PARA extraction lifecycle. `pending` when the sealed note has not yet been propagated into PARA entities, `done` after `para-extract` has processed it. Unset on `status: active` notes; set to `pending` at seal time.
- `last_updated` - ISO timestamp of the most recent write.
- `topics` - 3 to 8 short phrases. Specific enough to be useful, brief enough to scan.
- `people` - real people mentioned. Test: remove the name. Does the section lose something?
- `projects` - project names, lowercase, matching workspace conventions.
- `sessions` - 8-character prefixes of session ids that contributed content to this date. Attribution only; capture cursors for those sessions live in `memory/session-ledger.md`.

### Status transitions

- `active` - day is current or recent; content still arriving; `sessions-capture` may append.
- `sealed` - day has been closed by `daily-seal`; no further appends. Only material corrections allowed, and only with operator approval.

### Capture status transitions

- (unset) - capture is still in progress. Always the case for today's note. Also the case for past-days where the capture pipeline has not yet marked them complete.
- `done` - the heartbeat has determined that no more content can land in this note. The three conditions it checks:
  1. Date < today (workspace-local).
  2. `clawstodian/scripts/scan-sessions.py` reports `queue == 0` (no interactive session has unread content pending).
  3. For every ledger entry whose `dates_touched` includes this date: `lines_captured` equals the current transcript line count (session is fully captured) AND `last_activity` is strictly past end of this date (session has demonstrably moved on).

All three conditions together mean no turn with a date-X timestamp can still arrive from any session, so the note is safe to seal.

`daily-seal` reads `status: active` + `capture_status: done` as its queue. If the heartbeat is not running (gateway down, paused), `capture_status` does not get set and `daily-seal` does not fire - which is the correct behavior when the orchestrator is not there to supervise.

### PARA status transitions

- (unset) - note is not yet in the PARA queue (either `status: active` or a legacy sealed note predating this field).
- `pending` - note is `sealed` and queued for `para-extract`.
- `done` - `para-extract` has processed this note; PARA entities have been created or updated.

`para-extract` reads `status: sealed` + `para_status: pending` as its queue. Legacy sealed notes without `para_status` are not automatically queued.

## Note Structure

```markdown
---
(frontmatter)
---
# YYYY-MM-DD

Day summary - 2 to 3 sentences. What was this day about? Key outcomes.

---

## Descriptive topic - specific detail (~HH:MM UTC)

Content...

## Another topic (~HH:MM-HH:MM UTC)

Content...
```

### Rules

- Chronological order. Sections ordered by timestamp, earliest first.
- One section per topic. Multiple sessions on the same topic consolidate into one section.
- Descriptive headers. Searchable by `memory_search`. Include topic or project name, what happened, and timestamp.
- No duplicates. Overlapping content is merged, keeping the most complete version.
- No ops noise. Daily notes capture what happened, not which cron runs fired.
- Day summary after the date heading. Human-readable narrative, not a bullet list.
- Separator: `---` between the day summary and the first topic section.

## What to Capture

Include:
- Decisions and their rationale.
- Config or infrastructure changes.
- People with meaningful context.
- Project milestones.
- Problems and solutions.
- Learnings and workflow insights.
- Behavioral corrections from the user ("do not do X", "always do Y").

Skip:
- Greetings and acknowledgments.
- Temporary states.
- Raw tool output.
- Heartbeat or cron noise.
- Content already captured in a previous session.

## What Sealing Does

Sealing is purely editorial. No entity extraction, no `INDEX.md` updates. Entity extraction is handled by `para-extract` in a separate cron run.

On seal:
- Merge any topic-suffixed variants into the canonical note.
- Organize sections into chronological order.
- Merge duplicate sections from overlapping sessions.
- Remove noise (cron-run dumps, pipeline status).
- Write descriptive, searchable headers.
- Write a day summary.
- Curate frontmatter (topics, people, projects).
- Add thread-continuity markers when topics span days.
- Flip `status: active -> sealed` and set `para_status: pending`.

**Trivial-day fast-path:** a day with 2 or fewer sections and under 1 KB of body content seals by flipping `status` and setting `para_status: pending` without further editorial work.

## Session Ledger

The `sessions-capture` routine uses `memory/session-ledger.md` as its authoritative capture-state file: for each interactive session, the read cursor and dates touched. Only `sessions-capture` writes to it; the heartbeat reads it indirectly via `clawstodian/scripts/scan-sessions.py`.

### What goes in the ledger - interactive sessions only

**The ledger contains interactive sessions only.** Sessions that classify as skipped (cron-dispatched, hook-dispatched, sub-agents whose parent transcript owns the content, dreaming-routine sessions, delivery-only sessions with no real user turns) are NOT stored. Their classification is deterministic and cheap, so `scan-sessions.py` re-derives it on every scan rather than memoizing.

Benefits:
- The ledger stays small (the minority of sessions are interactive).
- No admission step - creating a ledger entry is always part of processing actual content, never a "just mark this so we don't re-examine it" write.
- Classification rules can evolve without needing to rewrite old ledger entries.

### Semantics

- **New interactive session** (present in `sessions_list`, absent from the ledger) - `scan-sessions.py` returns it with `status: new`. `sessions-capture` reads the JSONL from line 0, applies per-date, creates a new H2 entry in the ledger.
- **Stale interactive session** (ledger entry exists, but on-disk transcript line count exceeds `lines_captured`) - `scan-sessions.py` returns it with `status: stale`. `sessions-capture` reads from `lines_captured + 1` to end, applies per-date, advances the cursor.
- **Orphan ledger entry** (entry exists but session id is no longer in `sessions_list`) - ignored. Transcripts get pruned over time; old cursors just sit in the ledger as a historical record and do not gate anything.

The cursor advances only after the affected daily notes have been written successfully; a partial write leaves the cursor at its old position so the next firing retries.

### File shape

```markdown
<!-- template: clawstodian/session-ledger 2026-04-19 -->
# Session ledger

## 96a0c068-a1b2-c3d4-e5f6-7890abcdef12

- kind: direct
- first_seen: 2026-04-15T10:00Z
- last_activity: 2026-04-18T14:30Z
- lines_captured: 142
- dates_touched: 2026-04-15, 2026-04-16, 2026-04-17, 2026-04-18
- status: active
```

One H2 section per interactive session, in append order. Update cursor fields in place via narrow `Edit`. Never reorder existing sections.

### Fields

- **(heading)** - the full session id as returned by `sessions_list`.
- **kind** - from the `sessions_list` row (`direct`, `group`, `main`, etc. - shape depends on the OpenClaw version).
- **first_seen** - ISO-8601 UTC timestamp when this routine first wrote this entry.
- **last_activity** - the session's `updatedAt` at the most recent firing that captured from it. Mirrors the `sessions_list` row at capture time.
- **lines_captured** - the JSONL line count already processed. Next read starts at line `lines_captured + 1`.
- **dates_touched** - comma-separated `YYYY-MM-DD` list of daily notes this session has contributed to.
- **status** - `active` (session still receiving activity) | `dormant` (no activity for 7+ days but transcript still exists) | `done` (fully captured, session closed or more than 7 days old at admission time).

### Update rules

- Cursor advances happen via `Edit` with a narrow `old_string` (the exact line) so unrelated fields are never rewritten.
- New sessions are appended at the end as new H2 blocks. Do not insert them in the middle.
- Existing sections are never reordered; the file's chronological shape is the append order.
- Do not delete entries to match observed `sessions_list` state. If a transcript disappears, the orphan entry simply becomes inactive.

### What NOT to put in the ledger

- Skipped classifications (cron, hook, sub-agent, dreaming, delivery-only). These are derived on demand by `scan-sessions.py`.
- Full transcript content (lives on disk in the session JSONL files).
- Summaries of what happened in each session (lives in the daily notes).
- PARA extraction status (lives in the daily note's `para_status` frontmatter).
- Heartbeat tick records (live in `memory/heartbeat-trace.md`).

The ledger is strictly: "what have we captured from which interactive session, and how far did we get."

### Size tradeoff

On a disciplined workspace, interactive sessions accumulate slowly (the vast majority of new sessions are cron / hook / sub-agent / dreaming, all skipped). Ledgers of 100-300 entries are typical even after months of use; the file stays under 2000 lines, well within a single `Read` call.

### Why a flat markdown file and not JSON

The agent reads and writes this file with its normal `Read` / `Edit` tools. A structured JSON file would require a helper script to update one field safely; a markdown file with one H2 per session and one `- key: value` per attribute has the same read cost, narrower edits, and is operator-inspectable without tooling.
