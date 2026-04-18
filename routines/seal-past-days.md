# seal-past-days

Seal one unsealed past-day daily note per run with disk-fidelity. Drains the sealing queue one unit at a time.

## References

- Daily note format -> `memory/daily-note-structure.md`
- Today's note routine -> `clawstodian/routines/daily-note.md`
- PARA extractor -> `clawstodian/routines/para-extract.md`

Read `memory/daily-note-structure.md` before sealing. It defines the output format, frontmatter (including `para_status`), and the PARA handoff marker.

## Authority

- Edit `memory/YYYY-MM-DD.md` for past dates in seal form.
- Merge and delete `memory/YYYY-MM-DD-<slug>.md` siblings for past dates.
- Disable the `seal-past-days` cron via `openclaw cron disable` when the queue is empty.

## Approval gates

- No approval needed to seal a past-day note per the steps below.
- Ask before materially rewriting any content beyond what the seal steps specify.

## Escalation

- Note unreadable, API overload, disk IO error: surface what failed and why; do not silently skip.
- Conflicting content between canonical note and a slug sibling that cannot be merged without a judgment call: surface; do not choose.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

## Target selection

1. List `memory/YYYY-MM-DD.md` files where the date is before today (workspace local timezone).
2. Candidate = frontmatter `status: active`, OR the file is missing for a past date where `git log --since=YYYY-MM-DD --until=YYYY-MM-DD+1d` shows commits.
3. Pick the **oldest** candidate.

If no candidates exist, the queue is empty (see "After processing").

## Trivial-day fast-path

Before the full seal, inspect the note body (excluding frontmatter):
- Count `##` sections.
- Estimate body size.

If **<=2 sections and <=1KB body**, fast-path:
- Standardize frontmatter per `memory/daily-note-structure.md`.
- Write a 1-2 sentence day summary if missing.
- Flip `status: active` -> `status: sealed`.
- Leave or set `para_status: pending`.
- Update `last_updated`.
- Commit. Skip the merge / organize steps.

This prevents expensive compute on "quiet day - no user interactions" notes.

## Full seal

**Merge topic-suffixed variants.** Check for `memory/YYYY-MM-DD-*.md` (e.g. `memory/2026-04-07-ops-para-fix.md`). Read their content, merge into the canonical `memory/YYYY-MM-DD.md`, then delete the variants. If none exist, skip.

**Read the full daily note.** Understand it before changing anything.

**Gather authoritative inputs:**
- Raw session JSONL from disk for that date (authoritative record; `sessions_history` returns a safety-filtered view).
- `git log --since --until` for that date.
- `git diff` summaries for touched files.

**Organize the note:**
- Chronological order (by UTC timestamp).
- Merge duplicate sections covering the same topic.
- Every `##` header must be descriptive and searchable - `memory_search` matches on these. Include topic name + what happened + `(~HH:MM UTC)` timestamp.
- Write a 2-3 sentence day summary after the `# YYYY-MM-DD` heading: what was this day about?

**Remove noise.** Daily notes capture what *happened*, not which automations ran. Remove:
- Heartbeat digest output with no user interaction.
- Tick status sections (which tasks fired, which were skipped).
- Cron-run dumps unless they led to decisions or discussion.

**Curate frontmatter** per `memory/daily-note-structure.md`. Judgment calls:
- `people` - people the day was *about*. Remove-the-name test: if I remove this name, does the day's story change? Exclude internet strangers, bystanders, names in cron reminders.
- `projects` - same test. Include implicit work (work clearly serving a known project even without naming it). Exclude projects mentioned only in file paths.
- `topics` - 3-8 specific phrases. The day's themes, not a section-by-section list.

**Thread continuity.** When a section clearly continues work from a previous day, add `(continued from YYYY-MM-DD)` in the section body. Only when the continuation is unambiguous.

**Flip `status: active` -> `status: sealed`. Leave or set `para_status: pending`. Update `last_updated` to the current ISO timestamp.**

Do not perform PARA extraction here. `para-extract` owns sealed-note propagation into PARA.

## What to do

1. Run target selection.
2. If no candidate: the queue is empty; skip to "After processing".
3. Apply the trivial-day fast-path if the candidate qualifies. Otherwise run the full seal.
4. Process exactly one note, then stop. Multiple notes per run wastes budget and removes the isolation boundary between seals.

## After processing

1. Re-check the queue via target selection.
2. If queued notes remain, leave state as is.
3. If the queue is empty and this invocation was driven by the cron, disable the cron so it stops firing idle:

   ```bash
   openclaw cron disable seal-past-days
   ```

   In-session manual invocations can stop without touching cron state.

**Cron safety: disable means `openclaw cron disable`, NEVER `openclaw cron remove`.** Remove deletes the cron permanently.

## Commit

Add only the files you changed - never `git add -A` or `git add .`. Commit message: `memory: seal YYYY-MM-DD - <topic summary>`. Push immediately after the commit. No AI attribution lines.

## What NOT to do

- Do not drain multiple notes in a single run.
- Do not rewrite sealed note prose cosmetically beyond the seal steps.
- Do not perform PARA extraction inline; that is `para-extract`.
- Do not silently skip on failure; surface.

## Summary

Report one line:

```
seal-past-days YYYY-MM-DD: <sealed|skipped|failed> | sections N->N | para_status: pending | queue: <remaining> | cron: <enabled|disabled>
```
