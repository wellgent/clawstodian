# durable-insight

File things worth keeping beyond a daily note: decisions, resolved bugs, reusable patterns, named insights. Heartbeat-inline: runs inside `daily-notes-tend` or any other program when an insight surfaces during normal work.

## References

- PARA conventions -> `memory/para-structure.md`
- Workspace dashboard -> `MEMORY.md`

Read `memory/para-structure.md` before creating or moving an entity.

## Authority

- Create and edit files under `resources/`, `projects/<name>/README.md`, `areas/<kind>/<slug>.md`.
- Update `MEMORY.md` when a new project or top-level pointer is warranted.

## Trigger

- Folded into `daily-notes-tend` on each tick.
- Also ambient: when any program or normal turn produces a candidate insight, file it per this spec.

## Approval gates

- Obvious placement: file immediately.
- Ambiguous placement (multiple plausible homes, a new folder that does not exist yet, a topic crossing entities): ask the operator before filing.

## Escalation

If the insight implies a change to `AGENTS.md` rules, a workflow convention, or workspace structure, surface the proposal; do not edit authority documents unilaterally.

## What to do

1. Identify candidate insights from the recent session transcript, active workspace changes, or the program that invoked this one.
2. For each candidate: check whether an existing entity already covers it. If yes, update in place.
3. If no existing entity fits and placement is obvious, create the new entity per `memory/para-structure.md` naming.
4. If placement is ambiguous, batch the candidate for the tick's signalling and ask for direction before filing.
5. Report in the tick summary: list each file touched and a one-line reason.

## What NOT to do

- No stubs.
- No duplicate "lessons learned" files.
- No silent filing when placement was a guess.
- No reshuffling of existing entities for stylistic reasons.
- Do not create new top-level directories without operator approval.
