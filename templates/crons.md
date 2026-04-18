<!-- template: clawstodian/crons 2026-04-18 -->
# Cron jobs

Dashboard for this workspace's cron jobs. Authoritative state: `openclaw cron list --all`.

Every clawstodian routine runs as its own cron job. The heartbeat orchestrator does not execute routines; it only toggles burst workers based on workspace state.

Install commands live in `~/clawstodian/INSTALL_FOR_AGENTS.md` under "Cron install commands". The routine specs in `~/clawstodian/routines/` describe what each routine does, not how it is scheduled.

## daily-note

Keeps today's canonical daily note current. Appends session activity, merges slug siblings, files obvious durable insights.

- Schedule: `every 30m`
- Always enabled. Quiet runs reply `NO_REPLY` and stay silent.

## workspace-tidy

Removes trash, moves misplaced files to intuitive homes, maintains `.gitignore` for ephemeral files.

- Schedule: `every 2h`
- Always enabled. Quiet runs reply `NO_REPLY`.

## git-hygiene

Commits meaningful drift stage-by-path, pushes, maintains `.gitignore`.

- Schedule: `every 30m`
- Always enabled. Quiet runs reply `NO_REPLY`.

## seal-past-days

Seals one unsealed past-day daily note per run. Self-disables when the queue is empty.

- Schedule: `every 30m` (while enabled)
- Starts disabled. Heartbeat enables it when past-day notes with `status: active` exist.

## para-extract

Propagates one sealed daily note into PARA entities per run. Self-disables when the queue is empty.

- Schedule: `every 30m` (while enabled)
- Starts disabled. Heartbeat enables it when sealed notes with `para_status: pending` exist.

## para-align

Verifies PARA structural and semantic health (cross-references, naming, MEMORY.md currency). Applies trivial fixes; surfaces the rest.

- Schedule: `0 6 * * 0` (Sunday 06:00 UTC)
- Always enabled. Heartbeat may also `--wake now` mid-week on drift.

## Schedule overview

```
ALWAYS-ON CRONS
every 30m     daily-note
every 30m     git-hygiene
every 2h      workspace-tidy

HEARTBEAT-TOGGLED BURSTS (start disabled)
every 30m     seal-past-days
every 30m     para-extract

FIXED CRON
Sunday 06:00  para-align (UTC)
```

## System cron

OS-level crontab entries outside OpenClaw go here. Example:

```
0 2 * * * openclaw memory index 2>&1 | logger -t openclaw-reindex
```
