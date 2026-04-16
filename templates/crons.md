<!-- template: clawstodian/crons 2026-04-16 -->
# Cron jobs

Dashboard for this workspace's cron jobs. Authoritative state: `openclaw cron list --all`.

## close-of-day

Seals one past-day daily note per run with disk-fidelity. Self-disables when the queue is empty.

- Schedule: `every 30m` (while enabled)
- Starts disabled. Heartbeat `daily-notes-tend` enables it when past-day notes with `status: active` exist.

Install: `~/clawstodian/cron-recipes/close-of-day.md`.

## weekly-para-align

Verifies PARA structural integrity once per ISO week.

- Schedule: `0 6 * * 0` (Sunday 06:00, workspace timezone)
- Always enabled.

Install: `~/clawstodian/cron-recipes/weekly-para-align.md`.

## Schedule overview

```
DEMAND-DRIVEN (starts disabled)
every 30m     close-of-day

WEEKLY
Sunday 06:00  weekly-para-align
```

## System cron

OS-level crontab entries outside OpenClaw go here. Example:

```
0 2 * * * openclaw memory index 2>&1 | logger -t openclaw-reindex
```
