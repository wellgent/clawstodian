<!-- template: clawstodian/crons 2026-04-19 -->
# Cron jobs

Dashboard for this workspace's cron jobs. Authoritative state: `openclaw cron list --all`.

Every clawstodian routine runs as its own cron job. Two execution classes:

- **Scheduled** - fires on a wall-clock schedule; stays enabled; no self-disable.
- **Heartbeat-toggled burst** - starts disabled; the heartbeat enables it when a queue forms; the routine self-disables when it drains the queue.

Every firing in either class writes `memory/runs/<routine>/<ts>.md` and posts a channel summary. Routine specs live at `clawstodian/routines/<name>.md` (via the workspace symlink).

## clawstodian routines

### sessions-capture

Captures session transcripts into daily notes; self-disables on empty queue.

- **Schedule:** `every 30m` (while enabled)
- **State:** starts disabled; heartbeat toggles
- **Spec:** `clawstodian/routines/sessions-capture.md`

### daily-seal

Seals one unsealed past-day note per run; self-disables on empty queue.

- **Schedule:** `every 30m` (while enabled)
- **State:** starts disabled; heartbeat toggles
- **Spec:** `clawstodian/routines/daily-seal.md`

### para-extract

Propagates one sealed daily note into PARA entities per run; self-disables on empty queue.

- **Schedule:** `every 30m` (while enabled)
- **State:** starts disabled; heartbeat toggles
- **Spec:** `clawstodian/routines/para-extract.md`

### para-align

Weekly PARA health walk: structural integrity, cross-refs, semantic freshness, archive candidacy.

- **Schedule:** `0 6 * * 0` (Sunday 06:00 UTC)
- **State:** enabled
- **Spec:** `clawstodian/routines/para-align.md`

### workspace-clean

Weekly tree sweep: trash, misplaced files, orphaned dotfiles, `.gitignore` hygiene.

- **Schedule:** `0 7 * * 0` (Sunday 07:00 UTC)
- **State:** enabled
- **Spec:** `clawstodian/routines/workspace-clean.md`

### git-clean

Backstop commits for agents that did not commit themselves; twice daily.

- **Schedule:** `0 1,11 * * *` (01:00 and 11:00 UTC daily)
- **State:** enabled
- **Spec:** `clawstodian/routines/git-clean.md`

### health-check

Daily self-check on clawstodian machinery (heartbeat config, cron registrations, symlinks, markers).

- **Schedule:** `0 3 * * *` (03:00 UTC daily)
- **State:** enabled
- **Spec:** `clawstodian/routines/health-check.md`

## Other active jobs

Non-clawstodian cron jobs (memory indexing, release watchers, workspace-specific scheduled tasks) go here. `openclaw cron list --all` is authoritative; this section is a narrative dashboard for the operator.

## Schedule overview

```
SCHEDULED (always enabled)
Sunday 06:00        para-align       (UTC, weekly)
Sunday 07:00        workspace-clean  (UTC, weekly)
Daily 01:00 + 11:00 git-clean        (UTC, twice daily)
Daily 03:00         health-check     (UTC, daily)

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
