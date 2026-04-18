# daily-note

Keep today's canonical daily note current: append session activity, merge any `YYYY-MM-DD-slug.md` siblings, polish against conventions, file obvious durable insights inline.

## References

- Daily note format -> `memory/daily-note-structure.md`
- PARA conventions -> `memory/para-structure.md`
- Past-day sealer -> `clawstodian/routines/seal-past-days.md`

Read `memory/daily-note-structure.md` before writing. It defines frontmatter (including `para_status`), section rules, and the PARA handoff marker.

## Authority

- Create and edit `memory/YYYY-MM-DD.md` for today's date only.
- Merge and delete `memory/YYYY-MM-DD-<slug>.md` sibling files into today's canonical note (delete only after merging their content).
- File clearly durable insights surfaced during the pass into the appropriate PARA entity (obvious placements only; ambiguous ones surface in the summary).
- Read session transcripts via `sessions_list`, `sessions_history`, and raw JSONL from disk when fidelity matters.
- Update frontmatter fields defined in `memory/daily-note-structure.md`.

## Approval gates

- No approval needed for writes to today's active note or merges of today's slug siblings.
- No approval needed for filing an insight into a clearly-obvious PARA location.
- Ask before materially rewriting any sealed past-day note.
- Ask before filing an insight whose placement is ambiguous (multiple plausible homes, new top-level folder, crosses entities).

## Escalation

- If `sessions_list` returns nothing but `git log` shows commits for the day (or vice versa), surface the discrepancy in the summary and do not guess.
- If a slug sibling's content conflicts materially with the canonical note, surface the conflict and leave both files untouched until the operator resolves.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

## What to do

1. Determine today's date in workspace local time. Target: `memory/YYYY-MM-DD.md`.
2. Use today's note as the durable cursor: read its frontmatter, latest section, current body.
3. **Merge slug siblings.** Check `memory/YYYY-MM-DD-*.md`. For each: read, merge into canonical note under a descriptive section, delete the sibling file. Ambiguous merges surface in the summary instead.
4. **Append session activity.** Discover with `sessions_list`. Pull `sessions_history` for sessions with new activity or missing note coverage. Use `git log` for the same window. When the cursor is fuzzy, rescan a safe recent window and deduplicate against the note instead of guessing.
5. **Append only net-new material.** Do not rewrite existing sections cosmetically.
6. **File obvious durable insights inline.** If a decision, resolved bug, or reusable pattern clearly belongs in `resources/` or a project's `README.md`, file it now. Ambiguous insights surface in the summary.
7. **Update frontmatter** per `memory/daily-note-structure.md`: `status`, `last_updated`, `topics`, `people`, `projects`, `sessions`, and `para_status` (leave as set or initialize to `pending` per the structure spec).

## What NOT to do

- Do not create new `memory/YYYY-MM-DD-<slug>.md` files; merge any that exist into the canonical note.
- Do not reconstruct content for days with no evidence.
- Do not rewrite sealed notes cosmetically.
- Do not drain past-day backlog; that is `seal-past-days`.
- Do not auto-create new top-level directories for insight filing.
- Do not create stub PARA entities.

## Summary

When something changed, report one line:

```
daily-note YYYY-MM-DD: appended <N> sections | merged <M> slug siblings | filed <K> insights | <L> awaiting operator
```

When nothing changed, produce no summary. Under cron dispatch, return `NO_REPLY` so the run stays silent.
