# seal-past-days (routine)

Closes and finalizes one unsealed past-day note per firing per the daily-notes program. Editorial pass with disk-fidelity.

## Program

`clawstodian/programs/daily-notes.md` - follow its conventions, authority, approval gates, escalation rules, and what-NOT-to-do constraints. The program defines the workspace's daily-note lifecycle (`status: active -> sealed`, `para_status: pending`); this routine describes the cron's sealing procedure.

See `memory/daily-note-structure.md` for the format, frontmatter fields, and what the editorial pass keeps vs. removes.

## Target selection

1. List `memory/YYYY-MM-DD.md` files where the date is before today (workspace local timezone).
2. Candidate = frontmatter `status: active` AND `capture_status: done`. The heartbeat sets `capture_status: done` when it has verified that no more session content can land in the note (past-date, no pending admissions, all contributing sessions demonstrably past the date). See `memory/daily-note-structure.md` for the exact conditions.
3. Pick the **oldest** remaining candidate.

No time-based heuristics, no midnight grace. Sealing happens when the orchestrator has marked the day capture-complete. If the heartbeat is not running, `capture_status: done` does not get set and this routine does not fire - which is the correct behavior.

## Exec safety

- Run commands by exact path. No `eval`, `bash -c "..."`, or other indirection that hides the real command from the gateway's exec safety layer.
- For multi-line script logic, write the script to `/tmp/clawstodian-seal-<context>.py` (or `.sh`) and invoke it by path. Do not inline code via heredoc to an interpreter (`python3 <<EOF ... EOF`); the safety layer blocks that as obfuscation.
- `jq` and `python3 -c '<short expression>'` one-liners are fine when they fit on one line and the intent is obvious.

## Worker discipline

- One note per firing. Do not loop.
- Do not merge multiple days' content into one operation.
- If the program's approval gates say "surface" on a note, do not seal; surface the issue and stop.

## Trivial-day fast-path

Before the full seal, inspect the note body (excluding frontmatter). If **<=2 sections and <=1 KB body**:

- Standardize frontmatter per `memory/daily-note-structure.md`.
- Curate `topics`, `people`, `projects` from whatever content the note does have - a short day still has identifiable themes and people worth indexing, and missing them costs us searchability later.
- Write a 1-2 sentence day summary if missing.
- Flip `status: active` -> `status: sealed`.
- Leave or set `para_status: pending`.
- Update `last_updated`.
- Commit and push.

Skip the merge and full-organize steps. The point of the fast-path is to avoid expensive editorial compute on a "quiet day" note - not to skip curation.

## Full seal

1. **Merge topic-suffixed variants.** Check for `memory/YYYY-MM-DD-*.md`. Read, merge into canonical, delete the variants. If none, skip.
2. **Read the full daily note** and understand it before changing anything.
3. **Gather authoritative inputs:**
   - Raw session JSONL on disk for that date (the authoritative record; `sessions_history` is a safety-filtered view).
   - `git log --since --until` for that date.
   - `git diff` summaries for touched files.
4. **Organize the note:**
   - Chronological order (by UTC timestamp).
   - Merge duplicate sections covering the same topic.
   - Every `##` header descriptive and searchable: topic name + what happened + `(~HH:MM UTC)` timestamp.
   - Write a 2-3 sentence day summary after the `# YYYY-MM-DD` heading: what was this day about?
5. **Remove noise.** Heartbeat digest output with no user interaction, tick status sections, cron-run dumps unless they led to decisions or discussion.
6. **Curate frontmatter** per `memory/daily-note-structure.md`. Judgment calls:
   - `people` - remove-the-name test: if I remove this name, does the day's story change? Exclude internet strangers, bystanders, names in cron reminders.
   - `projects` - same test. Include implicit work. Exclude projects mentioned only in file paths.
   - `topics` - 3-8 specific phrases. The day's themes, not a section-by-section list.
7. **Thread continuity.** When a section clearly continues work from a previous day, add `(continued from YYYY-MM-DD)` in the section body. Only when the continuation is unambiguous.
8. **Flip `status: active` -> `status: sealed`.** Set `para_status: pending`. Update `last_updated` to the current ISO timestamp.

Do not perform PARA extraction here; that is `clawstodian/programs/para.md`'s domain (dispatched by the `para-extract` routine).

## Commit

Add only the files you changed - never `git add -A` or `git add .`. Commit message: `memory: seal YYYY-MM-DD - <topic summary>`. Push immediately.

## Self-disable on empty queue

After processing, re-run target selection. If the queue is empty, disable the cron:

```bash
openclaw cron disable seal-past-days
```

**Cron safety: disable means `openclaw cron disable`, NEVER `openclaw cron remove`.** Remove deletes the cron permanently.

## Run report

Two artifacts per firing: a full report written to disk and a single-line summary to the notifications channel.

### File on disk

Write to `memory/runs/seal-past-days/<YYYY-MM-DD>T<HH-MM-SS>Z.md`.

File shape:

```markdown
# seal-past-days run report

- timestamp: 2026-04-18T02:30:00Z
- target: memory/2026-04-17.md
- outcome: sealed | skipped | failed
- path: full | trivial-day-fast-path

## What happened

- Slug siblings merged: 0
- Sections before: 7
- Sections after: 5
- Noise removed: 2 heartbeat digest blocks
- Day summary written: yes
- Frontmatter curated: topics (5), people (2), projects (3)
- para_status set to: pending

## Queue after firing

- remaining past-active notes with capture_status: done - N
- cron state: enabled | disabled

## Commit

- <hash short> memory: seal 2026-04-17 - <topic>

## Channel summary

seal-past-days 2026-04-17: sealed (full) | sections 7->5 | para_status: pending | queue: 2 | cron: enabled | report: memory/runs/seal-past-days/2026-04-18T02-30-00Z.md
```

### Channel summary

```
seal-past-days YYYY-MM-DD: <sealed|skipped|failed> (<path>) | sections N->N | para_status: pending | queue: <remaining> | cron: <enabled|disabled> | report: memory/runs/seal-past-days/<ts>.md
```

`<path>` is `full` or `trivial-day-fast-path` - encodes which code path ran. Never return `NO_REPLY` on a seal attempt; every firing produces both a file and a channel post. A target-selection miss (no candidate qualifies) writes an abbreviated file with `outcome: skipped` (reason: no-target) and a one-line channel note.
