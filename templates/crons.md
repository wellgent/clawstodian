<!-- template: clawstodian/crons 2026-04-18 -->
# Cron jobs

Dashboard for this workspace's cron jobs. Authoritative state: `openclaw cron list --all`.

Every clawstodian routine runs as its own cron job. Each routine invokes a behavior from a program in `clawstodian/programs/`. The heartbeat orchestrator does not execute routines; it only toggles burst workers based on workspace state and posts an executive summary each tick.

Install commands live in `~/clawstodian/INSTALL.md` under "Cron install commands". Verification is in `~/clawstodian/VERIFY.md`. Removal is in `~/clawstodian/UNINSTALL.md`. Routine specs under `~/clawstodian/routines/` are thin dispatchers; program specs under `~/clawstodian/programs/` are the domain authorities.

## daily-note

Invokes `daily-notes` program: ingest recent session activity. Reads `sessions_list({activeMinutes: 360})` (6h window, sized to absorb gateway restarts up to that gap), advances per-session cursors in `memory/session-ledger.md`, appends to today's (and any still-active past day's) note, merges slug siblings, files obvious durable insights.

- Schedule: `every 30m`
- Always enabled. Quiet runs reply `NO_REPLY` and stay silent.

## backfill-sessions

Invokes `daily-notes` program: ingest one historical session per firing. Picks the oldest session from `sessions_list` that has no entry in `memory/session-ledger.md`. Classifies it, reads the full transcript, buckets by date, applies to active-date notes and surfaces bleed for sealed-date buckets. Self-disables when `sessions_list` count matches ledger entry count and no stale-cursor sessions remain.

- Schedule: `every 30m` (while enabled)
- Starts disabled. Heartbeat enables it when the session ledger is behind `sessions_list`.

## workspace-tidy

Invokes `workspace-tidy` program: walk and tidy. Removes trash, moves misplaced files to intuitive homes, maintains `.gitignore` for ephemeral files.

- Schedule: `every 2h`
- Always enabled. Quiet runs reply `NO_REPLY`.

## git-hygiene

Invokes `git-hygiene` program: commit drift. Commits meaningful changes stage-by-path, pushes, maintains `.gitignore`.

- Schedule: `every 30m`
- Always enabled. Quiet runs reply `NO_REPLY`.

## seal-past-days

Invokes `daily-notes` program: seal a past-day note. Seals one unsealed past-day daily note per run. Self-disables when the queue is empty.

- Schedule: `every 30m` (while enabled)
- Starts disabled. Heartbeat enables it when past-day notes with `status: active` exist.

## para-extract

Invokes `para` program: extract PARA from a sealed note. Propagates one sealed daily note into PARA entities per run. Self-disables when the queue is empty.

- Schedule: `every 30m` (while enabled)
- Starts disabled. Heartbeat enables it when sealed notes with `para_status: pending` exist.

## para-align

Invokes `para` program: align PARA structure. Verifies structural and semantic health (cross-references, naming, MEMORY.md currency). Applies trivial fixes; surfaces the rest.

- Schedule: `0 6 * * 0` (Sunday 06:00 UTC)
- Always enabled. Heartbeat may also `--wake now` mid-week on drift.

## Schedule overview

```
ALWAYS-ON CRONS
every 30m     daily-note
every 30m     git-hygiene
every 2h      workspace-tidy

HEARTBEAT-TOGGLED BURSTS (start disabled)
every 30m     backfill-sessions
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
