<!-- template: clawstodian/crons 2026-04-17 -->
# Cron jobs

Dashboard for this workspace's cron jobs. Authoritative state: `openclaw cron list --all`.

## close-of-day

Seals one past-day daily note per run with disk-fidelity. Self-disables when the queue is empty.

- Schedule: `every 30m` (while enabled)
- Starts disabled. Heartbeat `daily-notes-tend` enables it when past-day notes with `status: active` exist.

Install: `~/clawstodian/programs/close-of-day.md`.

## para-backfill

Propagates one sealed daily note into PARA per run. Self-disables when the queue is empty.

- Schedule: `every 30m` (while enabled)
- Starts disabled. Heartbeat enables it when sealed notes with `para_status: pending` exist.

Install: `~/clawstodian/programs/para-backfill.md`.

## weekly-para-align

Verifies PARA structural integrity once per ISO week.

- Schedule: `0 6 * * 0` (Sunday 06:00, workspace timezone)
- Always enabled.

Install: `~/clawstodian/programs/weekly-para-align.md`.

## Schedule overview

```
DEMAND-DRIVEN (starts disabled)
every 30m     close-of-day
every 30m     para-backfill

WEEKLY
Sunday 06:00  weekly-para-align
```

## System cron

OS-level crontab entries outside OpenClaw go here. Example:

```
0 2 * * * openclaw memory index 2>&1 | logger -t openclaw-reindex
```
