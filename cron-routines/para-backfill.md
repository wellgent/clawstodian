# para-backfill

Propagate one sealed daily note into PARA per run. Demand-driven: starts disabled; heartbeat enables it when a sealed-note queue exists; self-disables when the queue is empty.

## References

- Daily note format -> `memory/daily-note-structure.md`
- PARA conventions -> `memory/para-structure.md`
- Workspace dashboard -> `MEMORY.md`

Read `memory/daily-note-structure.md` and `memory/para-structure.md` before starting. They define the queue marker, note lifecycle, naming, and frontmatter rules.

## Queue definition

A note is queued for this worker only when all of the following are true:

- the note lives at `memory/YYYY-MM-DD.md`
- frontmatter `status: sealed`
- frontmatter `para_status: pending`

Do not infer a queue from missing fields or from vague staleness heuristics. Legacy sealed notes without `para_status` are not automatically queued.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters; the gateway's exec safety layer blocks that as obfuscation.

## Target selection

1. List canonical daily notes where frontmatter shows `status: sealed` and `para_status: pending`.
2. Pick the **oldest** queued note.

**Skip if:** no queued notes exist. Disable the cron and stop:

```bash
openclaw cron disable para-backfill
```

## What to do

Process exactly one queued note per run.

1. Read the full daily note.
2. Walk the note and detect candidate entities against `memory/para-structure.md` thresholds.
3. For each candidate:
   - obvious placement -> create or update in place
   - ambiguous placement -> do not create; surface it in the reply
4. Update any touched `INDEX.md` files.
5. Update root `MEMORY.md` only when a new project is listed.
6. Flip the note's `para_status` from `pending` to `done`. Leave `status: sealed` unchanged. Update `last_updated`.

## Worker discipline

- Process one note, then stop.
- Do not drain multiple notes in one run.
- Do not rewrite sealed note prose cosmetically while you are here. Only touch the frontmatter fields needed to mark queue progress.
- If you discover a substantive issue in the sealed note itself, surface it instead of silently rewriting beyond the queue marker.

## After processing

1. Re-check the queue.
2. If queued notes remain, leave the cron enabled.
3. If the queue is empty, disable the cron:

```bash
openclaw cron disable para-backfill
```

**Cron safety: disable means `openclaw cron disable`, NEVER `openclaw cron remove`.** Remove deletes the cron permanently.

## Commit

Add only the files you changed, never `git add -A` or `git add .`. Commit message: `para: backfill YYYY-MM-DD - <summary>`. Push immediately after the commit. No AI attribution lines.

## Failure handling

If any step fails, do NOT disable the cron. Surface what failed and why so the next slot can retry and the health sweep can catch repeated failures.

## Reply

Single line summary to the session:

```text
para-backfill YYYY-MM-DD: <processed|skipped|failed> | entities <n updated, m created, k ambiguous> | queue: <remaining> | cron: <enabled|disabled>
```

## Install

Prerequisite: the workspace has a `clawstodian/` directory with symlinks to the package's `cron-routines/*.md` files. If you are adding this routine later, create the symlink first:

```bash
mkdir -p clawstodian
ln -sf ~/clawstodian/cron-routines/para-backfill.md clawstodian/para-backfill.md
```

Register the cron with operator confirmation. Starts disabled; heartbeat enables it on demand.

```bash
openclaw cron add \
  --name para-backfill \
  --every 30m \
  --disabled \
  --session isolated \
  --light-context \
  --no-deliver \
  --message "Read clawstodian/para-backfill.md and execute."
```

## Verify

```bash
openclaw cron list --all | grep para-backfill
```

Shows the job as disabled when the queue is empty.

## Uninstall

```bash
openclaw cron remove para-backfill
```
