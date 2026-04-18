# seal-past-days (routine)

Seals one past-day note per firing per the daily-notes program.

## Program

`clawstodian/programs/daily-notes.md` - follow the "Seal a past-day note" behavior (including target selection, trivial-day fast-path, and full seal steps).

## Target

The oldest candidate returned by the program's target selection (past date, `status: active` or missing with commits for that day, respecting the 2h midnight grace for yesterday).

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters; the gateway's exec safety layer blocks that as obfuscation.

## Worker discipline

- One note per firing. Do not loop.
- Do not merge multiple days' content into one operation.
- If the program's approval gates say "surface" on a note, do not seal; surface it and stop.

## Self-disable on empty queue

After processing, re-run target selection. If the queue is empty, disable the cron:

```bash
openclaw cron disable seal-past-days
```

**Cron safety: disable means `openclaw cron disable`, NEVER `openclaw cron remove`.** Remove deletes the cron permanently.

## Run report

Single line delivered to the logs channel by the cron runner:

```
seal-past-days YYYY-MM-DD: <sealed|skipped|failed> | sections N->N | para_status: pending | queue: <remaining> | cron: <enabled|disabled>
```

Never return `NO_REPLY` on a seal attempt; even fast-path success is worth reporting.
