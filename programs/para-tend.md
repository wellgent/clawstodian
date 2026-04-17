# para-tend

Maintain the structured PARA graph extracted from daily notes and direct activity. Heartbeat-direct: one sealed-note pass per tick. Deep structural verification is owned by `weekly-para-align`; bulk backfill is owned by `para-backfill`.

## References

- PARA conventions -> `memory/para-structure.md`
- Daily note format -> `memory/daily-note-structure.md`
- Workspace dashboard -> `MEMORY.md`
- Weekly audit -> `clawstodian/programs/weekly-para-align.md`
- Bulk backfill worker -> `clawstodian/programs/para-backfill.md`

Read `memory/para-structure.md` before creating or moving entities.

## Authority

- Create and edit files in `projects/`, `areas/`, `resources/`, `archives/`.
- Maintain `INDEX.md` in each.
- Update `MEMORY.md` dashboard when a new project is listed.

## Trigger

- Heartbeat task `para-tend` on each tick.
- Do not replace `weekly-para-align` structural verification.
- Do not replace `para-backfill` bulk queue draining.

## Approval gates

- Auto-create when the entity is clearly in bounds per `memory/para-structure.md` thresholds (a project with a goal and deliverable; a person with context in 2+ notes; a resource capturing a named pattern; a server that belongs in `areas/servers/`).
- Ask before creating when placement or entity boundary is ambiguous, or when the candidate crosses types.

## Escalation

Surface drift: frontmatter violations, stale `last_updated`, orphaned `related:` pointers. Propose a fix; do not silently normalize.

## What to do

1. Select one sealed daily note not yet processed (detect by comparing note's `last_updated` against entity `last_updated` for entities it references).
2. Walk the note and detect candidate entities against the thresholds in `memory/para-structure.md`.
3. For each candidate: obvious placement -> create or update; ambiguous -> batch for operator.
4. Update `INDEX.md` in the relevant PARA folder when entities are created, renamed, or archived.
5. Update `MEMORY.md` dashboard when a new project is listed.

## What NOT to do

- No stubs.
- No re-foldering of existing entities without asking.
- No condensing or rewriting entities for stylistic reasons.
- No inventing `related:` pointers.
- No `INDEX.md` rewrites that remove existing entries.
- No bulk draining - that's `para-backfill`.
