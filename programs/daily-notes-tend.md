# daily-notes-tend

Keep one canonical daily note per calendar day with activity. Heartbeat-direct: executed by `HEARTBEAT.md` on each tick.

## References

- Daily note format -> `memory/daily-note-structure.md`
- Companion program -> `clawstodian/programs/durable-insight.md` (run inline while tending)
- Burst worker for past days -> `clawstodian/programs/close-of-day.md`

Read `memory/daily-note-structure.md` before writing. It defines frontmatter, section rules, and the PARA handoff marker.

## Authority

- Create and edit `memory/YYYY-MM-DD.md`.
- Read session transcripts via `sessions_list` and `sessions_history`, and read raw JSONL from disk when fidelity matters.
- Update frontmatter fields defined in `memory/daily-note-structure.md`.

## Trigger

Heartbeat task `daily-notes-tend` every tick, coordinated by `HEARTBEAT.md`. Past-day sealing is not this program's job - enqueue via `close-of-day` burst worker.

## Approval gates

- No approval for writes to today's active note.
- Ask before materially rewriting any sealed past-day note.

## Escalation

If `sessions_list` returns nothing but `git log` shows commits for the day (or vice versa), surface the discrepancy in the tick summary and do not guess.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

## What to do

1. Determine today's date in workspace local time. Target: `memory/YYYY-MM-DD.md`.
2. Use today's note as the durable cursor: read its frontmatter, latest section, and current body before appending.
3. Discover session activity with `sessions_list`. Pull `sessions_history` for sessions with new activity or missing note coverage. Use `git log` for the same window.
4. If the cursor is fuzzy, rescan a safe recent window and deduplicate against the note instead of guessing.
5. Append only net-new material. Do not rewrite existing sections cosmetically.
6. Update frontmatter: `status`, `last_updated`, `topics`, `people`, `projects`, `sessions`, and the daily-note queue fields defined in `memory/daily-note-structure.md`.
7. If durable insights surface during the pass, run `durable-insight` inline.

## What NOT to do

- Do not create `memory/YYYY-MM-DD-<topic>.md` topic-suffixed variants.
- Do not reconstruct content for days with no evidence.
- Do not rewrite sealed notes cosmetically.
- Do not do backlog drain for past days inline - that is the `close-of-day` burst worker's job.
