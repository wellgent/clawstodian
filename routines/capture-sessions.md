# capture-sessions (routine)

Every 30 minutes while enabled. Processes one session's unread JSONL tail into the appropriate daily note(s) per the daily-notes program.

Starts disabled. The heartbeat orchestrator enables this cron when it detects capture gaps (un-admitted sessions in `sessions_list`, or ledger entries whose `last_activity` is behind the matching `sessions_list` row's `updatedAt`) and disables it when both counts return to zero.

This routine is the **backstop** for the daily-notes program. Agents working in live sessions are the primary writers of daily notes; this cron catches what they miss - forgotten end-of-session updates, cut-off contexts, sub-agent and cron-kind sessions that never touched the note, gateway outages, fresh installs over existing history.

## Program

`clawstodian/programs/daily-notes.md` - follow the "Capture one session's new content" behavior (including gap enumeration, target selection, classification, turn filtering, date bucketing, and cursor-advance discipline).

## Target

The single session with the newest `updatedAt` among those with a gap:

- **un-admitted**: present in `sessions_list` but absent from `memory/session-ledger.md`.
- **stale**: present in ledger, but `sessions_list` row's `updatedAt > ledger.last_activity`.

Selecting by newest `updatedAt` prioritizes live operator sessions over historical drain. On a fresh install against an existing workspace, this means today's DM session lands first; yesterday's, the day before that, ... continue to drain in the background at 30m cadence.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

## Worker discipline

- One session per firing. Do not loop to the next gap even if capacity remains.
- Read JSONL with `Read` from `lines_captured + 1` (or offset 0 for a newly-admitted interactive session). Do not re-read from 0 when the ledger has a cursor.
- Write daily-note updates FIRST, then advance the ledger cursor. If either step fails, leave the cursor at its old position so the next firing retries.
- Never mutate a sealed daily note. Content for a sealed date goes into the `bleed_over` accumulator.
- Cursor edits to `memory/session-ledger.md` are narrow `Edit` calls on the matching lines, not full rewrites.

## Self-disable on empty queue

After processing, re-check both gap conditions: un-admitted count AND stale-cursor count. If both are zero, disable the cron:

```bash
openclaw cron disable capture-sessions
```

**Cron safety: disable means `openclaw cron disable`, NEVER `openclaw cron remove`.** Remove deletes the cron permanently.

## Run report

Single line delivered to the logs channel by the cron runner:

```
capture-sessions <sid-prefix>: <captured|admitted-skipped|failed> | classification: <interactive|skipped:<reason>> | lines: <from>-><to> | dates: [YYYY-MM-DD, ...] | merged <M> slugs | filed <K> insights | bleed <B> sealed | queue: un-admitted=<u>/stale=<s> | cron: <enabled|disabled>
```

Return `NO_REPLY` when the firing's only outcome was admitting a `skipped`-classified session (cron, hook, subagent, delivery-only). These admissions are frequent during initial backfill on a populated workspace and reporting every one creates channel fatigue without carrying useful information.

Always report: interactive captures, failures, queue-becomes-empty self-disable firings.
