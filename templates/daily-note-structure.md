<!-- template: clawstodian/daily-note-structure 2026-04-18 -->
# Daily Note Structure

Single source of truth for the daily note model. The `capture-sessions`, `seal-past-days`, and `para-extract` routines (defined in `AGENTS.md` under clawstodian) read this file. Customize per workspace as needed.

## Overview

Daily notes live at `memory/YYYY-MM-DD.md`. Each file represents exactly one calendar day.

**The primary writer of daily notes is the agent working in session with the operator.** Per the workspace's memory-maintenance rules, any agent doing notable work appends to today's note as the work happens. That is the default path.

The `capture-sessions` cron is the **backstop**: it catches sessions that did not get fully written up in-session, including sub-agent sessions, cron-kind sessions, gateway-outage gaps, and historical sessions that predate a clawstodian install. Past days are sealed by `seal-past-days`. PARA entities get extracted from sealed notes by `para-extract`.

**One canonical file per day.** The primary daily note is always `memory/YYYY-MM-DD.md`. Topic-suffixed variants such as `memory/YYYY-MM-DD-foo.md` may appear during active sessions; the `capture-sessions` routine merges them into the canonical note when it next processes a session touching that date, and `seal-past-days` merges them on seal for past dates. Sealed notes never have topic-suffixed siblings.

**Capture state lives in the ledger, not the note.** Per-session cursors (how far each session transcript has been read) live in `memory/session-ledger.md`. Daily notes reference sessions only by id; the `sessions:` frontmatter field is a human-readable attribution list, not capture state.

```
agent in-session (primary)             capture-sessions (burst backstop)        seal-past-days (burst)              para-extract (burst)
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
- `status` - `active` while the day is still receiving content, `sealed` after `seal-past-days` has finalized it.
- `para_status` - PARA extraction lifecycle. `pending` when the sealed note has not yet been propagated into PARA entities, `done` after `para-extract` has processed it. Omit or leave empty on `status: active` notes; set to `pending` at seal time.
- `last_updated` - ISO timestamp of the most recent write.
- `topics` - 3 to 8 short phrases. Specific enough to be useful, brief enough to scan.
- `people` - real people mentioned. Test: remove the name. Does the section lose something?
- `projects` - project names, lowercase, matching workspace conventions.
- `sessions` - 8-character prefixes of session ids that contributed content to this date. Attribution only; capture cursors for those sessions live in `memory/session-ledger.md`.

### Status transitions

- `active` - day is current or recent; content still arriving; `capture-sessions` may append.
- `sealed` - day has been closed by `seal-past-days`; no further appends. Only material corrections allowed, and only with operator approval.

### PARA status transitions

- (unset) - note is `active`; not in the PARA queue yet.
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
