# para-extract

Propagate one sealed daily note into PARA entities per run. Burst worker: starts disabled; heartbeat enables when sealed-note queue exists; self-disables when the queue is empty.

## References

- Daily note format -> `memory/daily-note-structure.md`
- PARA conventions -> `memory/para-structure.md`
- Workspace dashboard -> `MEMORY.md`
- Past-day sealer -> `clawstodian/routines/seal-past-days.md`
- PARA structural health -> `clawstodian/routines/para-align.md`

Read `memory/daily-note-structure.md` and `memory/para-structure.md` before starting. They define the queue marker, note lifecycle, naming, and frontmatter rules.

## Authority

- Create and edit files in `projects/`, `areas/`, `resources/`, `archives/`.
- Maintain `INDEX.md` in each PARA folder.
- Update root `MEMORY.md` when a new project is listed.
- Flip `para_status: pending -> done` on the processed note.
- Toggle this cron's enabled state via `openclaw cron disable` when the queue is empty.

## Queue definition

A note is queued for this worker only when all of the following are true:

- the note lives at `memory/YYYY-MM-DD.md`
- frontmatter `status: sealed`
- frontmatter `para_status: pending`

Do not infer a queue from missing fields or from vague staleness heuristics. Legacy sealed notes without `para_status` are not automatically queued.

## Trigger

Every 30 minutes while enabled (see Install). Starts disabled. Heartbeat enables when queue is non-empty; self-disables on empty queue.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters; the gateway's exec safety layer blocks that as obfuscation.

## Target selection

1. List canonical daily notes where frontmatter shows `status: sealed` and `para_status: pending`.
2. Pick the **oldest** queued note.

**Skip if:** no queued notes exist. Disable the cron and stop:

```bash
openclaw cron disable para-extract
```

## Approval gates

- **Obvious placement** (a project with a goal and deliverable; a person with context in 2+ notes; a resource capturing a named pattern; a server that belongs in `areas/servers/`): auto-create or update in place per `memory/para-structure.md` thresholds.
- **Ambiguous placement** (multiple plausible homes, crosses entity types, new top-level folder): do not create; surface in the reply.

## Escalation

- Frontmatter violations, orphaned `related:` pointers, stale `last_updated`: do not silently normalize; propose the fix in the reply. (Structural alignment is `para-align`'s job.)
- A sealed note whose content is substantively wrong (contradictory, corrupted): surface; do not attempt to rewrite.

## What to do

Process exactly one queued note per run.

1. Read the full daily note.
2. Walk the note and detect candidate entities against `memory/para-structure.md` thresholds (projects, areas/people, areas/companies, areas/servers, resources).
3. For each candidate:
   - obvious placement -> create or update in place
   - ambiguous placement -> surface in the reply without creating
4. Update any touched `INDEX.md` files.
5. Update root `MEMORY.md` only when a new project is listed.
6. Flip the note's `para_status` from `pending` to `done`. Leave `status: sealed` unchanged. Update `last_updated`.

## Worker discipline

- Process one note, then stop.
- Do not drain multiple notes in one run.
- Do not rewrite sealed note prose cosmetically while you are here. Only touch the frontmatter fields needed to mark queue progress.
- Do not invent `related:` pointers.
- Do not create stubs.

## After processing

1. Re-check the queue.
2. If queued notes remain, leave the cron enabled.
3. If the queue is empty, disable the cron:

```bash
openclaw cron disable para-extract
```

**Cron safety: disable means `openclaw cron disable`, NEVER `openclaw cron remove`.** Remove deletes the cron permanently.

## Commit

Add only the files you changed, never `git add -A` or `git add .`. Commit message: `para: extract YYYY-MM-DD - <summary>`. Push immediately after the commit. No AI attribution lines.

## Failure handling

If any step fails, do NOT disable the cron. Surface what failed and why so the next slot can retry.

## Reply

Single line summary. The runner announces it to the logs channel:

```
para-extract YYYY-MM-DD: <processed|skipped|failed> | entities <N updated, M created, K ambiguous> | queue: <remaining> | cron: <enabled|disabled>
```

## Install

Prerequisite: `clawstodian/routines` symlink to `~/clawstodian/routines`.

```bash
openclaw cron add \
  --name para-extract \
  --every 30m \
  --disabled \
  --session isolated \
  --light-context \
  --announce --channel discord --to "channel:<your-logs-channel-id>" \
  --message "Read clawstodian/routines/para-extract.md and execute."
```

Starts disabled; heartbeat enables on demand. Substitute `--no-deliver` for silent runs.

## Verify

```bash
openclaw cron list --all | grep para-extract
```

Shows the job as disabled at install time.

## Uninstall

```bash
openclaw cron remove para-extract
```
