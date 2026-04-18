# backfill-sessions (routine)

Every 30 minutes while enabled. Drains the historical-session queue one session per run per the daily-notes program.

Starts disabled. The heartbeat orchestrator enables this cron when the `sessions_list` count exceeds the number of entries in `memory/session-ledger.md`, and disables it when the ledger is caught up.

This routine exists so that fresh installs on already-populated workspaces, and any session that slipped past the `daily-note` routine's 6-hour steady-state window, eventually get captured into daily notes without the always-on cron having to do a full rescan every tick.

## Program

`clawstodian/programs/daily-notes.md` - follow the "Ingest a historical session" behavior (including target selection, classification, and one-session-per-firing discipline).

## Target

One of:

- The oldest session by `updatedAt` returned by `sessions_list({limit: 500})` that has no entry in `memory/session-ledger.md` (admission gap; the common case).
- A session that IS in the ledger but whose `last_activity` is more than 6h behind the matching `sessions_list` row's `updatedAt` (stale cursor; happens after an extended gateway outage). Process these before any un-admitted sessions so capture gaps close first.

If both kinds exist, prefer stale-cursor sessions over un-admitted ones. Within each kind, pick the oldest.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

## Worker discipline

- Process exactly one session per firing. Do not drain the queue in a single run.
- Classify the session before reading its transcript; if `skipped`, append the ledger entry and stop.
- For `interactive` sessions, read the entire transcript, bucket by date, and apply each bucket per the program's rules.
- Most historical sessions will only touch sealed dates; those buckets go to the `bleed_over` accumulator in the run report, not into the sealed notes.
- Append the ledger entry only after daily-note writes for active dates succeed.

## Self-disable on empty queue

After processing, re-check both signals: the admission gap (`sessions_list` count vs. ledger entry count) AND the stale-cursor count (ledger entries whose `last_activity` lags the matching row's `updatedAt` by more than 6h). If BOTH are zero, disable the cron so idle firings stop:

```bash
openclaw cron disable backfill-sessions
```

**Cron safety: disable means `openclaw cron disable`, NEVER `openclaw cron remove`.** Remove deletes the cron permanently.

## Run report

Single line delivered to the logs channel by the cron runner:

```
backfill-sessions <session-id-prefix>: <captured|skipped|failed> | classification: <interactive|skipped:<reason>> | lines: N | dates: [YYYY-MM-DD, ...] | bleed: <count> sealed | queue: <remaining> | cron: <enabled|disabled>
```

Return `NO_REPLY` on runs whose only work was admitting a `skipped`-classified session to the ledger (cron / hook / subagent / delivery-only). These are frequent during the initial backfill drain on a populated workspace and reporting each one creates channel fatigue without carrying useful information. Captures (interactive sessions), failures, and queue-becomes-empty self-disable runs are always worth seeing - never `NO_REPLY` those.
