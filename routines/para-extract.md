# para-extract

Propagate one sealed daily note into PARA entities per run. Drains the PARA-extraction queue one note at a time.

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
- Disable the `para-extract` cron via `openclaw cron disable` when the queue is empty.

## Queue definition

A note is queued for extraction only when all of the following are true:

- the note lives at `memory/YYYY-MM-DD.md`
- frontmatter `status: sealed`
- frontmatter `para_status: pending`

Do not infer a queue from missing fields or from vague staleness heuristics. Legacy sealed notes without `para_status` are not automatically queued.

## Approval gates

- **Obvious placement** (a project with a goal and deliverable; a person with context in 2+ notes; a resource capturing a named pattern; a server that belongs in `areas/servers/`): auto-create or update in place per `memory/para-structure.md` thresholds.
- **Ambiguous placement** (multiple plausible homes, crosses entity types, new top-level folder): do not create; surface in the summary.

## Escalation

- Frontmatter violations, orphaned `related:` pointers, stale `last_updated`: do not silently normalize; propose the fix in the summary. (Structural alignment is `para-align`'s job.)
- A sealed note whose content is substantively wrong (contradictory, corrupted): surface; do not attempt to rewrite.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

## Target selection

1. List canonical daily notes where frontmatter shows `status: sealed` and `para_status: pending`.
2. Pick the **oldest** queued note.

If no queued notes exist, the queue is empty (see "After processing").

## What to do

Process exactly one queued note per run.

1. Read the full daily note.
2. Walk the note and detect candidate entities against `memory/para-structure.md` thresholds (projects, areas/people, areas/companies, areas/servers, resources).
3. For each candidate:
   - obvious placement -> create or update in place
   - ambiguous placement -> surface in the summary without creating
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
2. If queued notes remain, leave state as is.
3. If the queue is empty and this invocation was driven by the cron, disable the cron so it stops firing idle:

   ```bash
   openclaw cron disable para-extract
   ```

   In-session manual invocations can stop without touching cron state.

**Cron safety: disable means `openclaw cron disable`, NEVER `openclaw cron remove`.** Remove deletes the cron permanently.

## Commit

Add only the files you changed, never `git add -A` or `git add .`. Commit message: `para: extract YYYY-MM-DD - <summary>`. Push immediately after the commit. No AI attribution lines.

## What NOT to do

- Do not drain multiple notes in one run.
- Do not rewrite sealed note content beyond the `para_status` and `last_updated` frontmatter fields.
- Do not auto-normalize structural drift; surface it for `para-align`.

## Summary

Report one line:

```
para-extract YYYY-MM-DD: <processed|skipped|failed> | entities <N updated, M created, K ambiguous> | queue: <remaining> | cron: <enabled|disabled>
```
