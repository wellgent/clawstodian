# para-extract (routine)

Processes one sealed note per firing, reconciling its content against the PARA knowledge graph - updating existing entities the note touches and creating new ones where content clears creation thresholds.

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

1. **Read the full sealed daily note.**
2. **Read the PARA indices for comprehension.** Load `projects/INDEX.md`, `areas/INDEX.md`, `resources/INDEX.md`. These enumerate existing entities; keep them available as you walk the note. Spot-check root `MEMORY.md` if the note touches the active-projects dashboard. Updating-first requires knowing what is already there.
3. **Walk the note for candidate subjects** (projects, people, companies, servers, reusable patterns). For each candidate, match against the indices:
   - **Match found -> UPDATE in place.** Read the entity. Apply the changes the note implies: revise `status` or next steps on a project, record a dated decision or outcome on an area/person/company page, sharpen a resource with the new insight, touch `last_updated`, add a `related:` pointer when a new connection is now explicit. Do not rewrite existing prose cosmetically.
   - **No match + clears thresholds in `memory/para-structure.md` -> CREATE** in the right bucket with required frontmatter.
   - **No match + thresholds not cleared -> skip.** Content remains in the daily note; a future day's additional mention may clear the threshold later.
   - **Ambiguous match (multiple plausible targets) or ambiguous placement -> surface** in the run report without acting.
4. **Update touched `INDEX.md` files.** Creations add entries; updates normally do not require INDEX changes unless the entity's title or visible status shifted.
5. **Update root `MEMORY.md`** only when a new project is listed or an active project retires.
6. **Flip the note's `para_status`** from `pending` to `done`. Leave `status: sealed` unchanged. Update the note's `last_updated`.

Update is the common case; a sealed note typically touches more entities than it introduces.

## Commit

Add only the files you changed. Commit message: `para: extract YYYY-MM-DD - <summary>`. Push immediately.

## Exec safety

- Run commands by exact path. No `eval`, `bash -c "..."`, or other indirection that hides the real command from the gateway's exec safety layer.
- For multi-line script logic, write the script to `/tmp/clawstodian-para-extract-<context>.py` (or `.sh`) and invoke it by path. Do not inline code via heredoc to an interpreter (`python3 <<EOF ... EOF`); the safety layer blocks that as obfuscation.
- `jq` and `python3 -c '<short expression>'` one-liners are fine when they fit on one line and the intent is obvious.

## Worker discipline

- One note per firing. Do not drain the queue in a single run.
- Touch the daily note's frontmatter only to mark queue progress (`para_status`, `last_updated`). Do not rewrite the sealed note's prose.
- On PARA entities, apply the updates the note's content implies; do not rewrite existing entity prose cosmetically (per `programs/para.md`).
- Do not invent `related:` pointers.
- Do not create stubs.
- If approval gates say "surface" - whether for creation or an ambiguous update target - do not act; surface in the run report.

## Self-disable on empty queue

After processing, re-check the queue. If empty, disable the cron. `openclaw cron disable` takes the job id, not the name - resolve name -> id first:

```bash
ID=$(openclaw cron list --json | jq -r '.jobs[] | select(.name=="para-extract") | .id')
openclaw cron disable "$ID"
```

**Cron safety: disable means `openclaw cron disable`, NEVER `openclaw cron rm`.** Rm deletes the cron permanently.

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
