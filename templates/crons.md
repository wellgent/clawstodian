<!-- template: clawstodian/crons 2026-04-18 -->
# Cron jobs

Dashboard for this workspace's cron jobs. Authoritative state: `openclaw cron list --all`.

Every clawstodian routine runs as its own cron job. Each routine invokes a behavior from a program in `clawstodian/programs/`. The heartbeat orchestrator does not execute routines; it only toggles burst workers based on workspace state and posts an executive summary each tick.

Install commands live in `~/clawstodian/INSTALL.md` under "Cron install commands". Verification is in `~/clawstodian/VERIFY.md`. Removal is in `~/clawstodian/UNINSTALL.md`. Routine specs under `~/clawstodian/routines/` are thin dispatchers; program specs under `~/clawstodian/programs/` are the domain authorities.

## capture-sessions

Invokes `daily-notes` program: capture one session's unread JSONL into the appropriate daily notes. Picks the session with the newest `updatedAt` among those with a gap (un-admitted in ledger, or stale cursor). Classifies if new, reads JSONL from `lines_captured + 1` to end, buckets by timestamp into daily notes, advances the cursor. Merges slug siblings and files obvious insights when today's bucket is touched. Self-disables when no gaps remain.

- Schedule: `every 30m` (while enabled)
- Starts disabled. Heartbeat enables it when the ledger has un-admitted sessions or stale cursors.
- Backstop only: agents in live sessions are the primary writers of daily notes per `AGENTS.md` memory rules; this cron catches what they miss.

## workspace-tidy

Invokes `workspace-tidy` program: walk and tidy. Removes trash, moves misplaced files to intuitive homes, maintains `.gitignore` for ephemeral files.

- Schedule: `every 2h`
- Always enabled. Every firing produces a run-report file + channel post (quiet firings post `outcome: clean`).

## git-hygiene

Invokes `git-hygiene` program: commit drift. Commits meaningful changes stage-by-path, pushes, maintains `.gitignore`.

- Schedule: `every 30m`
- Always enabled. Every firing produces a run-report file + channel post (quiet firings post `outcome: clean`).

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
every 30m     git-hygiene
every 2h      workspace-tidy

HEARTBEAT-TOGGLED BURSTS (start disabled)
every 30m     capture-sessions
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
