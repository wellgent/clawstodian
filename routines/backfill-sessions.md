# backfill-sessions (routine)

Every 30 minutes while enabled. Drains the historical-session queue one session per run per the daily-notes program.

Starts disabled. The heartbeat orchestrator enables this cron when the `sessions_list` count exceeds the number of entries in `memory/session-ledger.md`, and disables it when the ledger is caught up.

This routine exists so that fresh installs on already-populated workspaces, and any session that slipped past the `daily-note` routine's 90-minute steady-state window, eventually get captured into daily notes without the always-on cron having to do a full rescan every tick.

## Program

`clawstodian/programs/daily-notes.md` - follow the "Ingest a historical session" behavior (including target selection, classification, and one-session-per-firing discipline).

## Target

The oldest session by `updatedAt` returned by `sessions_list({limit: 500})` that has no entry in `memory/session-ledger.md`.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

## Worker discipline

- Process exactly one session per firing. Do not drain the queue in a single run.
- Classify the session before reading its transcript; if `skipped`, append the ledger entry and stop.
- For `interactive` sessions, read the entire transcript, bucket by date, and apply each bucket per the program's rules.
- Most historical sessions will only touch sealed dates; those buckets go to the `bleed_over` accumulator in the run report, not into the sealed notes.
- Append the ledger entry only after daily-note writes for active dates succeed.

## Self-disable on empty queue

After processing, re-check: if `sessions_list` count equals the ledger entry count, disable the cron so idle firings stop:

```bash
openclaw cron disable backfill-sessions
```

**Cron safety: disable means `openclaw cron disable`, NEVER `openclaw cron remove`.** Remove deletes the cron permanently.

## Run report

Single line delivered to the logs channel by the cron runner:

```
backfill-sessions <session-id-prefix>: <captured|skipped|failed> | classification: <interactive|skipped:<reason>> | lines: N | dates: [YYYY-MM-DD, ...] | bleed: <count> sealed | queue: <remaining> | cron: <enabled|disabled>
```

Never return `NO_REPLY` on a backfill attempt; each run is a state transition worth seeing.
