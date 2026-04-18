<!-- template: clawstodian/crons 2026-04-18 -->
# Cron jobs

Dashboard for this workspace's cron jobs. Authoritative state: `openclaw cron list --all`.

Every clawstodian routine runs as its own cron job. Each routine invokes a behavior from a program in `clawstodian/programs/`. Two execution classes: **scheduled** routines fire on a wall-clock schedule (stay enabled, no self-disable); **heartbeat-toggled bursts** start disabled and the heartbeat turns them on when a gap is detected, off when drained.

Every firing in either class produces a run-report file at `memory/runs/<routine>/<ts>.md` and a channel post. The heartbeat is the orchestrator: it toggles bursts based on workspace state, watches run reports for items the routines surfaced to the operator, and posts an executive summary each tick.

Install commands live in `~/clawstodian/INSTALL.md` under "Cron install commands". Verification is in `~/clawstodian/VERIFY.md`. Removal is in `~/clawstodian/UNINSTALL.md`. Routine specs under `~/clawstodian/routines/` are thin dispatchers; program specs under `~/clawstodian/programs/` are the domain authorities.

## sessions-capture

Invokes `daily-notes` program: capture one session's unread JSONL into the appropriate daily notes. Picks the session with the newest `updatedAt` among those with a gap (un-admitted in ledger, or stale cursor). Classifies if new, reads JSONL from `lines_captured + 1` to end, buckets by timestamp into daily notes, advances the cursor. Merges slug siblings and files obvious insights when today's bucket is touched. Self-disables when no gaps remain.

- Schedule: `every 30m` (while enabled)
- Starts disabled. Heartbeat enables it when the ledger has un-admitted sessions or stale cursors.
- Backstop only: agents in live sessions are the primary writers of daily notes per `AGENTS.md` memory rules; this cron catches what they miss.

## workspace-clean

Invokes `workspace` program: walk and tidy. Removes trash, moves misplaced files to intuitive homes, maintains `.gitignore` for ephemeral files, prunes run-report files older than 30 days.

- Schedule: `0 7 * * 0` (Sunday 07:00 UTC, right after `para-align`)
- Scheduled (always enabled, no self-disable). Every firing produces a run-report file + channel post (quiet firings post `outcome: clean`).

## git-clean

Invokes `repo` program: commit drift. Backstop for agents who commit themselves per the program's convention. Commits meaningful changes stage-by-path, pushes, maintains `.gitignore`.

- Schedule: `0 1,11 * * *` (01:00 and 11:00 UTC daily)
- Scheduled (always enabled, no self-disable). Twice-daily cadence is the safety net; agents commit their own work in-session. Operators with specific preferences can adjust the cron expression.

## daily-seal

Invokes `daily-notes` program: seal a past-day note. Seals one unsealed past-day daily note per run. Self-disables when the queue is empty.

- Schedule: `every 30m` (while enabled)
- Starts disabled. Heartbeat enables it when past-day notes with `status: active` AND `capture_status: done` exist.

## para-extract

Invokes `para` program: extract PARA from a sealed note. Propagates one sealed daily note into PARA entities per run. Self-disables when the queue is empty.

- Schedule: `every 30m` (while enabled)
- Starts disabled. Heartbeat enables it when sealed notes with `para_status: pending` exist.

## para-align

Invokes `para` program: align PARA structure. Verifies structural and semantic health (cross-references, naming, MEMORY.md currency). Applies trivial fixes; surfaces the rest.

- Schedule: `0 6 * * 0` (Sunday 06:00 UTC)
- Scheduled (always enabled). Heartbeat may also `--wake now` mid-week on drift reported by `para-extract`.

## Schedule overview

```
SCHEDULED (always enabled)
Sunday 06:00        para-align       (UTC, weekly)
Sunday 07:00        workspace-clean  (UTC, weekly)
Daily 01:00 + 11:00 git-clean        (UTC, twice daily)

HEARTBEAT-TOGGLED BURSTS (start disabled; heartbeat enables on gap)
every 30m           sessions-capture
every 30m           daily-seal
every 30m           para-extract
```

## System cron

OS-level crontab entries outside OpenClaw go here. Example:

```
0 2 * * * openclaw memory index 2>&1 | logger -t openclaw-reindex
```
