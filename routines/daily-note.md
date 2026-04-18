# daily-note (routine)

Every 30 minutes, always enabled. Tends today's canonical daily note per the daily-notes program by ingesting recent session activity.

This routine is the steady-state arm of session capture. It covers sessions with activity in the last 90 minutes via `sessions_list({activeMinutes: 90})` and advances each one's cursor in `memory/session-ledger.md`. Historical sessions (older than the 90-minute window with no ledger entry) are handled by the `backfill-sessions` burst worker, not by this routine.

## Program

`clawstodian/programs/daily-notes.md` - follow the "Ingest recent activity" behavior.

## Target

`memory/YYYY-MM-DD.md` for today's workspace-local date. Also yesterday's note when a session's new lines bucket to yesterday and the note is still `status: active`. Sealed past notes are never modified; bleed-over goes to the run report.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

## Worker discipline

- One pass per firing. No internal loops.
- Stop after discovering sessions, classifying new ones, advancing cursors for those with new content, merging slug siblings, filing obvious insights, and updating frontmatter.
- Cursor advances happen via narrow `Edit` calls against `memory/session-ledger.md`; never rewrite the whole ledger.
- If the program's approval gates say "surface", do not act.
- If `sessions_list` returns zero rows and the visibility config appears correct, surface as an anomaly; do not silently succeed.

## Run report

Single line delivered to the logs channel by the cron runner:

```
daily-note YYYY-MM-DD: sessions <active>/<captured>/<new-skipped> | appended <N> sections | merged <M> slugs | filed <K> insights | bleed <B> sealed | <L> awaiting operator
```

Where:
- `active` = sessions returned by `sessions_list({activeMinutes: 90})`.
- `captured` = sessions whose ledger cursor advanced this run.
- `new-skipped` = sessions newly classified as `skipped` and added to the ledger.
- `bleed` = sessions whose new lines contained content for sealed dates (not applied, surfaced).

Return `NO_REPLY` when zero sessions were active and no slug siblings existed, so no-change runs stay silent.
