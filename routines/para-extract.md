# para-extract (routine)

Processes one sealed note per firing, propagating its content into the PARA knowledge graph.

## Program

`clawstodian/programs/para.md` - conventions, authority, approval gates, and escalation.

## Queue definition

A daily note is queued for extraction only when all of the following are true:

- the note lives at `memory/YYYY-MM-DD.md`
- frontmatter `status: sealed`
- frontmatter `para_status: pending`

Legacy sealed notes without `para_status` are not automatically queued.

## Target selection

1. List canonical daily notes where frontmatter shows `status: sealed` and `para_status: pending`.
2. Pick the **oldest** queued note.

## Steps

1. Read the full daily note.
2. Walk the note and detect candidate entities against `memory/para-structure.md` thresholds (projects, areas/people, areas/companies, areas/servers, resources).
3. For each candidate:
   - Obvious placement -> create or update in place.
   - Ambiguous placement -> surface in the run report without creating.
4. Update any touched `INDEX.md` files.
5. Update root `MEMORY.md` only when a new project is listed.
6. Flip the note's `para_status` from `pending` to `done`. Leave `status: sealed` unchanged. Update `last_updated`.

## Commit

Add only the files you changed. Commit message: `para: extract YYYY-MM-DD - <summary>`. Push immediately.

## Exec safety

- Run commands by exact path. No `eval`, `bash -c "..."`, or other indirection that hides the real command from the gateway's exec safety layer.
- For multi-line script logic, write the script to `/tmp/clawstodian-para-extract-<context>.py` (or `.sh`) and invoke it by path. Do not inline code via heredoc to an interpreter (`python3 <<EOF ... EOF`); the safety layer blocks that as obfuscation.
- `jq` and `python3 -c '<short expression>'` one-liners are fine when they fit on one line and the intent is obvious.

## Worker discipline

- One note per firing. Do not drain the queue in a single run.
- Touch only the frontmatter fields needed to mark queue progress (`para_status`, `last_updated`). Do not rewrite sealed note prose cosmetically.
- Do not invent `related:` pointers.
- Do not create stubs.
- If approval gates say "surface" on a candidate entity, do not create; surface it in the run report.

## Self-disable on empty queue

After processing, re-check the queue. If empty, disable the cron:

```bash
openclaw cron disable para-extract
```

**Cron safety: disable means `openclaw cron disable`, NEVER `openclaw cron remove`.** Remove deletes the cron permanently.

## Run report

Two artifacts per firing: a full report on disk following the shared run-report shape, and a multi-line scannable summary posted to the notifications channel.

### File on disk

Write to `memory/runs/para-extract/<YYYY-MM-DD>T<HH-MM-SS>Z.md`.

```markdown
# para-extract run report

- timestamp: 2026-04-18T03:00:00Z
- context: 2026-04-17
- outcome: processed
- cron_state: enabled → disabled

## What happened

- target: memory/2026-04-17.md
- para_status transition: pending → done
- entities updated: 3
  - areas/people/alice.md
  - projects/vps-migration/README.md
  - resources/1password-secrets-management.md
- entities created: 1
  - areas/companies/pulsy.md
- entities ambiguous (surfaced, not acted on): 0

## Queue after firing

- remaining sealed notes with para_status: pending - 0
- cron state: disabled

## Commits

- def5678 para: extract 2026-04-17 - VPS migration entities

## Surfaced for operator

- (none)

## Channel summary

para-extract · 2026-04-17 · processed
Entities: 3 updated · 1 created · 0 ambiguous
Commit: def5678 para: extract 2026-04-17 - VPS migration entities
Queue: 0 sealed-pending notes · cron: disabled
Report: memory/runs/para-extract/2026-04-18T03-00-00Z.md
```

### Channel summary

Multi-line. One insight per line:

```
para-extract · <date> · <outcome>
Entities: <U> updated · <C> created · <A> ambiguous
Commit: <hash short> <subject>
Queue: <N> sealed-pending notes · cron: <enabled|disabled>
Report: memory/runs/para-extract/<ts>.md
```

- `outcome` is `processed | skipped | failed`.
- If ambiguous is non-zero, also append a "Surfaced" list in the file (channel stays at five lines).

Never return `NO_REPLY`; every firing is a meaningful PARA transition and produces both artifacts.
