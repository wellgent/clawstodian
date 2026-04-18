# daily-notes

The workspace maintains one canonical daily note per calendar day at `memory/YYYY-MM-DD.md`, capturing activity, decisions, and context that happened that day. The note is the primary timeline record for the workspace.

## Who writes

**The primary writer of daily notes is the agent working in session with the operator.** Per `AGENTS.md` memory-maintenance rules, any agent doing notable work appends to today's note as the work happens, commits, and pushes. This is the default path.

Under cron, `sessions-capture`, `daily-seal`, and `para-extract` operate on the same notes - catching what in-session agents missed, closing past days, and propagating sealed notes into PARA. Each routine has its own spec; this program defines the conventions all of them (and in-session agents) follow.

## References

- Daily note format, frontmatter, what-to-capture rules, and session-ledger format -> `memory/daily-note-structure.md`.
- PARA extraction program that reads sealed notes -> `clawstodian/programs/para.md`.

Read `memory/daily-note-structure.md` before writing.

## Conventions

- **One canonical file per day.** `memory/YYYY-MM-DD.md`. Never two canonical files for the same date.
- **Slug siblings are transient.** Files like `memory/YYYY-MM-DD-<slug>.md` may appear during active sessions; merge them into the canonical note. Sealed days never have siblings.
- **Lifecycle:**
  - `status: active` while the day is current and content is still arriving (today plus any past date not yet sealed).
  - `status: sealed` after the editorial pass has finalized the day.
- **Capture readiness:**
  - `capture_status: done` set by the heartbeat when no more session content can land in this note (past-day, no pending sessions, all contributing sessions demonstrably past the date). `daily-seal` reads `status: active` + `capture_status: done` as its queue.
  - Unset while capture may still land content.
- **PARA handoff:**
  - `para_status: pending` set at seal time; queues the note for PARA extraction.
  - `para_status: done` set after PARA extraction completes.

## Authority

- Create and edit `memory/YYYY-MM-DD.md` for today or any unsealed past date.
- Merge and delete `memory/YYYY-MM-DD-<slug>.md` siblings into the canonical file.
- Update frontmatter fields defined in `memory/daily-note-structure.md`.

PARA entity writes are out of scope here; they are governed by `clawstodian/programs/para.md`, which in-session agents follow in parallel.

Must NOT rewrite sealed notes cosmetically. Must NOT write into a sealed note: content intended for a sealed date surfaces as an anomaly (in-session: ask the operator in chat; under cron dispatch: include it in the routine's run report).

## Approval gates

- **Obvious placement -> act.** Appending today's notable moment, merging an obvious slug sibling.
- **Ambiguous placement -> surface.** A slug sibling whose content conflicts materially with the canonical note. In-session: ask the operator. Under cron dispatch: include in the run report.
- **Past-date content for a sealed note -> surface, do not apply.** The operator decides whether to reopen the seal.
- **Material rewrite of a sealed note -> ask.** Only allowed with explicit operator approval.

## Escalation

- If the target note is unreadable, corrupted, or in an unexpected encoding -> surface and stop.
- If a slug sibling's content conflicts materially with the canonical note -> surface the conflict and leave both files untouched until the operator resolves.

## What NOT to do

- Do not create `memory/YYYY-MM-DD-<slug>.md` new files; merge any that exist into the canonical note.
- Do not reconstruct content for days with no evidence.
- Do not rewrite sealed notes cosmetically.
- Do not write into a sealed note at all; surface as an anomaly instead.
- Do not store cursor state in daily-note frontmatter; the session ledger is authoritative (format in `memory/daily-note-structure.md`).
