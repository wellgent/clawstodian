# close-of-day

Seal one unsealed past-day daily note per run. Demand-driven: starts disabled; heartbeat `daily-notes-tend` enables when past-day notes accumulate; self-disables when the queue is empty.

## References

- Daily note format -> `memory/daily-note-structure.md`
- PARA conventions -> `memory/para-structure.md`

Read `memory/daily-note-structure.md` before sealing. It defines the output format. Do not reinvent it here.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters; the gateway's exec safety layer blocks that as obfuscation.

## Target selection

1. List `memory/YYYY-MM-DD.md` files where the date is before today (workspace local timezone).
2. Candidate = frontmatter `status: active`, OR the file is missing for a past date where `git log --since=YYYY-MM-DD --until=YYYY-MM-DD+1d` shows commits.
3. Pick the **oldest** candidate.

**Skip if:** no candidates exist. Disable the cron and stop:

```bash
openclaw cron disable close-of-day
```

## Trivial-day fast-path

Before the full seal, inspect the note body (excluding frontmatter):
- Count `##` sections.
- Estimate body size.

If **<=2 sections and <=1KB body**, fast-path:
- Standardize frontmatter per `memory/daily-note-structure.md`.
- Write a 1-2 sentence day summary if missing.
- Flip `status: active` -> `status: sealed`. Update `last_updated`.
- Commit. Skip the merge / organize / PARA steps.

This prevents expensive compute on "quiet day - no user interactions" notes.

## Full seal

**Merge topic-suffixed variants.** Check for `memory/YYYY-MM-DD-*.md` (e.g. `memory/2026-04-07-ops-para-fix.md`). These are variants created outside the sealing pipeline - during interactive sessions, by other tools, or by manual edits. Read their content, merge into the canonical `memory/YYYY-MM-DD.md`, then delete the variants. If none exist, skip.

**Read the full daily note.** Understand it before changing anything.

**Gather authoritative inputs:**
- Raw session JSONL from disk for that date (authoritative record; `sessions_history` returns a safety-filtered view).
- `git log --since --until` for that date.
- `git diff` summaries for touched files.

**Organize the note:**
- Chronological order (by UTC timestamp).
- Merge duplicate sections covering the same topic (common when multiple sessions touched the same work).
- Every `##` header must be descriptive and searchable - `memory_search` matches on these. Include topic name + what happened + `(~HH:MM UTC)` timestamp.
- Write a 2-3 sentence day summary after the `# YYYY-MM-DD` heading: what was this day about?

**Remove noise.** Daily notes capture what *happened*, not which automations ran. Remove:
- Heartbeat digest output with no user interaction.
- Tick status sections (which tasks fired, which were skipped).
- Cron-run dumps unless they led to decisions or discussion.

**Curate frontmatter** per `memory/daily-note-structure.md`. Judgment calls:
- `people` - people the day was *about*. Remove-the-name test: if I remove this name, does the day's story change? Exclude internet strangers, bystanders in group chats, names in cron reminders.
- `projects` - same test. Include implicit work (work that clearly serves a known project even without naming it). Exclude projects mentioned only in file paths.
- `topics` - 3-8 specific phrases. The day's themes, not a section-by-section list.

**Thread continuity.** When a section clearly continues work from a previous day (same project, topic, or person interaction spanning days), add `(continued from YYYY-MM-DD)` in the section body. Only when the continuation is unambiguous.

**Flip `status: active` -> `status: sealed`. Update `last_updated` to the current ISO timestamp.**

## PARA entity detection

After sealing, walk the note and detect candidates per `memory/para-structure.md` thresholds:
- **Obvious placement** (existing entity, or clear new entity matching naming): create or update in place.
- **Ambiguous placement**: do NOT create. Note the candidate in the reply so the next heartbeat `para-tend` surfaces it to the operator.

Update any touched `INDEX.md`. Update root `MEMORY.md` only when a new project is listed.

## After processing

**Process exactly one daily note per run, then stop.** The cron fires every 30m while enabled; processing multiple days in a single run wastes budget and removes the isolation boundary between seals (a hallucination in day 1 could bleed into day 2).

1. **Check queue.** Re-run target selection. Any more candidates?
2. **If none:** disable the cron:

   ```bash
   openclaw cron disable close-of-day
   ```

The cron stays dormant until the heartbeat `daily-notes-tend` re-enables it when new past-day notes accumulate.

**Cron safety: disable means `openclaw cron disable`, NEVER `openclaw cron remove`.** Remove deletes the cron permanently.

## Commit

Add only the files you changed - never `git add -A` or `git add .`. Commit message: `memory: seal YYYY-MM-DD - <topic summary>`. No AI attribution lines (`Co-Authored-By`, `Generated by`, etc.).

## Failure handling

If any step fails (note unreadable, API overload, disk IO error): do NOT disable the cron - the next slot retries. Do NOT silently skip. The reply surfaces what failed and why. The heartbeat `workspace-sweep` health check catches repeated failures and surfaces them to the operator.

## Reply

Single line summary to the session. The cron runs `--no-deliver`, so this lands nowhere external - but the session transcript captures it for the health sweep:

```
close-of-day YYYY-MM-DD: <sealed|skipped|failed> | sections N->N | PARA <n created, m ambiguous> | queue: <remaining> | cron: <enabled|disabled>
```

## Install

Prerequisite: the workspace has a `clawstodian/` directory with symlinks to the package's `cron-routines/*.md` files. `INSTALL_FOR_AGENTS.md` creates this during setup; if you are adding this routine later, create the symlink first:

```bash
mkdir -p clawstodian
ln -sf ~/clawstodian/cron-routines/close-of-day.md clawstodian/close-of-day.md
```

Register the cron with operator confirmation. Starts disabled; the heartbeat enables on demand.

```bash
openclaw cron add \
  --name close-of-day \
  --every 30m \
  --disabled \
  --session isolated \
  --light-context \
  --no-deliver \
  --message "Read clawstodian/close-of-day.md and execute."
```

## Verify

```bash
openclaw cron list --all | grep close-of-day
```

Shows the job as disabled.

## Uninstall

```bash
openclaw cron remove close-of-day
```
