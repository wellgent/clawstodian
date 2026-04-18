# daily-notes

The workspace maintains one canonical daily note per calendar day at `memory/YYYY-MM-DD.md`, capturing activity, decisions, and context that happened that day. The note is the primary timeline record for the workspace.

## References

- Daily note format and frontmatter -> `memory/daily-note-structure.md`
- PARA extraction program that reads sealed notes -> `clawstodian/programs/para.md`

Read `memory/daily-note-structure.md` before writing. It defines frontmatter (including `para_status`), section rules, and the PARA handoff marker.

## Conventions

- **One canonical file per day.** The primary daily note is always `memory/YYYY-MM-DD.md`. Never two canonical files for the same date.
- **Slug siblings are transient.** Files like `memory/YYYY-MM-DD-<slug>.md` may appear during active sessions but must be merged into the canonical note. Sealed days never have slug siblings.
- **Lifecycle**:
  - `status: active` while the day is current and content is still arriving.
  - `status: sealed` after editorial pass has finalized the day.
- **PARA handoff**:
  - `para_status: pending` set at seal time to queue the note for PARA extraction.
  - `para_status: done` set after PARA extraction completes.
- **Sources of truth**: `sessions_list`, `sessions_history`, raw session JSONL (authoritative when fidelity matters), `git log`, workspace diffs, the agent's own observations.

## Authority

- Create and edit `memory/YYYY-MM-DD.md` for any date.
- Merge and delete `memory/YYYY-MM-DD-<slug>.md` siblings into the canonical file.
- Read session transcripts via `sessions_list`, `sessions_history`, and raw JSONL.
- Flip lifecycle markers on past-day notes (`status: active -> sealed`, `para_status: pending`).
- Update frontmatter fields defined in `memory/daily-note-structure.md`.
- File clearly durable insights surfaced during a pass into obvious PARA locations (`resources/<descriptive-slug>.md`, `projects/<name>/README.md` when the insight is scoped to a project). Ambiguous filings surface for operator decision.

Must NOT rewrite sealed notes cosmetically or for stylistic reasons.

## Approval gates

- **Obvious placement -> act.** Appending to today's note, merging an obvious slug sibling, filing an insight into a clearly-right location.
- **Ambiguous placement -> surface.** An insight that could live in multiple PARA buckets, a slug sibling whose content conflicts with the canonical note, a new top-level folder. In-session: ask the operator. Via cron dispatch: include in the run report so the operator sees it in the logs channel.
- **Material rewrite of a sealed note -> ask.** Only allowed with explicit operator approval.

## Escalation

- If `sessions_list` returns nothing but `git log` shows commits for the day (or vice versa), surface the discrepancy and do not guess at the day's activity.
- If a slug sibling's content conflicts materially with the canonical note, surface the conflict and leave both files untouched until the operator resolves.
- If the target note is unreadable, corrupted, or in an unexpected encoding, surface and stop.

## Behaviors

### Tend today's note

Keep today's canonical note current throughout the day.

1. Determine today's date in workspace local time. Target: `memory/YYYY-MM-DD.md`.
2. Use today's note as the durable cursor: read its frontmatter, latest section, current body before appending.
3. **Merge slug siblings.** Check `memory/YYYY-MM-DD-*.md`. For each: read, merge into canonical note under a descriptive section, delete the sibling file. Ambiguous merges surface instead.
4. **Append session activity.** Discover sessions with `sessions_list`. Pull `sessions_history` for sessions with new activity or missing note coverage. Use `git log` for the same window. When the cursor is fuzzy, rescan a safe recent window and deduplicate against the note instead of guessing.
5. **Append only net-new material.** Do not rewrite existing sections cosmetically.
6. **File obvious durable insights inline.** If a decision, resolved bug, or reusable pattern clearly belongs in `resources/` or a project's `README.md`, file it now. Ambiguous insights surface instead.
7. **Update frontmatter** per `memory/daily-note-structure.md`: `status`, `last_updated`, `topics`, `people`, `projects`, `sessions`, and `para_status` (leave as set or initialize to `pending` per the structure spec when appropriate).

### Seal a past-day note

Close and finalize one unsealed past-day note with disk-fidelity.

**Target selection** (for cron-driven sealing of the oldest unsealed note):

1. List `memory/YYYY-MM-DD.md` files where the date is before today (workspace local timezone).
2. Candidate = frontmatter `status: active`, OR the file is missing for a past date where `git log --since=YYYY-MM-DD --until=YYYY-MM-DD+1d` shows commits.
3. Pick the **oldest** candidate.

**Trivial-day fast-path.** Before the full seal, inspect the note body (excluding frontmatter). If **<=2 sections and <=1KB body**:

- Standardize frontmatter per `memory/daily-note-structure.md`.
- Write a 1-2 sentence day summary if missing.
- Flip `status: active` -> `status: sealed`.
- Leave or set `para_status: pending`.
- Update `last_updated`.
- Commit.

Skip the merge and organize steps. This prevents expensive compute on "quiet day - no user interactions" notes.

**Full seal.**

1. **Merge topic-suffixed variants.** Check for `memory/YYYY-MM-DD-*.md`. Read, merge into canonical, delete the variants. If none, skip.
2. **Read the full daily note** and understand it before changing anything.
3. **Gather authoritative inputs:**
   - Raw session JSONL from disk for that date (authoritative record; `sessions_history` returns a safety-filtered view).
   - `git log --since --until` for that date.
   - `git diff` summaries for touched files.
4. **Organize the note:**
   - Chronological order (by UTC timestamp).
   - Merge duplicate sections covering the same topic.
   - Every `##` header must be descriptive and searchable. Include topic name + what happened + `(~HH:MM UTC)` timestamp.
   - Write a 2-3 sentence day summary after the `# YYYY-MM-DD` heading: what was this day about?
5. **Remove noise.** Daily notes capture what *happened*, not which automations ran. Remove heartbeat digest output with no user interaction, tick status sections, cron-run dumps unless they led to decisions or discussion.
6. **Curate frontmatter** per `memory/daily-note-structure.md`. Judgment calls:
   - `people` - remove-the-name test: if I remove this name, does the day's story change? Exclude internet strangers, bystanders, names in cron reminders.
   - `projects` - same test. Include implicit work. Exclude projects mentioned only in file paths.
   - `topics` - 3-8 specific phrases. The day's themes, not a section-by-section list.
7. **Thread continuity.** When a section clearly continues work from a previous day, add `(continued from YYYY-MM-DD)` in the section body. Only when the continuation is unambiguous.
8. **Flip `status: active` -> `status: sealed`.** Leave or set `para_status: pending`. Update `last_updated` to the current ISO timestamp.

Do not perform PARA extraction here. That responsibility belongs to `clawstodian/programs/para.md`.

**Commit.** Add only the files you changed, never `git add -A` or `git add .`. Commit message: `memory: seal YYYY-MM-DD - <topic summary>`. Push immediately.

## What NOT to do

- Do not create `memory/YYYY-MM-DD-<slug>.md` new files; merge any that exist into the canonical note.
- Do not reconstruct content for days with no evidence.
- Do not rewrite sealed notes cosmetically.
- Do not perform PARA extraction as part of tending or sealing.
- Do not auto-create new top-level directories for insight filing.
- Do not create stub PARA entities.
- Do not batch multiple past-day seals in one pass; one note per invocation.
