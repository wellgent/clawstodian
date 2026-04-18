# Writing a clawstodian program

Programs are the unit of authority in clawstodian. A program is a markdown spec under `programs/` that describes how a workspace domain is governed - conventions, authority, approval gates, escalation rules, and the full set of behaviors the agent can perform in that domain.

Programs are read by agents at session bootstrap (via `AGENTS.md`) and by cron-dispatched routines that execute specific behaviors on a schedule. Programs are the source of truth for behavior. Routines are thin dispatchers that reference programs.

## Program vs routine

The distinction is **what** vs **when**.

- **Program**: "this is how we operate this workspace in domain X." Domain-shaped, time-agnostic. Contains conventions, authority, approval gates, escalation, and behaviors. Read at bootstrap by every agent. Changes only when the convention itself evolves.
- **Routine**: "run this instruction set at this cadence." Schedule-shaped. Contains target, run report format, worker discipline, install command. Read only inside cron dispatch. Multiple routines can reference the same program.

Before writing a program, ask: is this a new domain the workspace operates in, or a new invocation of an existing domain? New domain -> program. New invocation -> see `writing-a-routine.md`.

## Anatomy

Every program uses the same anatomy. Section order matters - agents read top-to-bottom to understand the domain.

```markdown
# <program-name>

<One or two sentences describing the domain this program governs.>

## References

- Convention docs this program relies on (e.g. `memory/daily-note-structure.md`).
- Related programs.

## Conventions

Durable facts about this domain: file naming, lifecycle states, frontmatter, directory structure, any invariants the agent must respect.

## Authority

What the agent is permitted to do in this domain. What it must not touch. Tools it uses.

## Approval gates

Which actions are obvious (just act) vs ambiguous (surface for operator). Explain what "surface" means in this domain (in-session: ask; via cron: include in routine run report).

## Escalation

Unusual states that halt the program's behaviors and surface for operator judgment.

## Exec safety

(Optional.) If the program uses shell: run commands by exact path, no heredocs piped into shell interpreters, etc.

## Behaviors

Named, discrete operations the program performs. One `### <behavior>` subsection per behavior. Each subsection has explicit numbered steps. Routines pick which behavior to invoke.

### <behavior 1>

Ordered steps.

### <behavior 2>

Ordered steps.

## What NOT to do

Prohibitions specific to this program.
```

The program contains all the steps a behavior needs. Routines should be able to invoke a behavior by name without duplicating the steps.

## Programs can have multiple behaviors

A single program often governs multiple related behaviors. The daily-notes program covers:

- Tending today's note
- Sealing a past-day note

Both operate on `memory/YYYY-MM-DD.md` files and share the same conventions, authority, approval gates, and frontmatter rules. They're distinct enough to need different step lists, but they belong in one domain authority. A single file holds both.

This pattern generalizes: if two operations share conventions and authority, put them in one program as separate behaviors. If two operations have genuinely different authority or conventions, separate programs.

## Approval gate and escalation language

Programs support two invocation contexts: in-session (agent is working with the user) and cron-dispatched (isolated session, no user). The language should work for both.

- "Obvious placement -> act." Applies everywhere.
- "Ambiguous placement -> surface." In-session: ask the operator in chat. Via cron: include in the routine's run report so the operator sees it in the logs channel.

Use "surface" rather than "ask" throughout; clarify the context distinction once at the top of Approval gates if useful, or in a workspace-level convention.

## Catalog integration

When you ship a new program:

- Add it to the Programs catalog in `templates/AGENTS.md` with a one-sentence domain description. Workspaces with older copies of the template will pull the update on their next refresh.
- If routines need to invoke its behaviors, add or update the relevant `routines/<name>.md` files.
- If this program introduces new conventions that reference docs, update or add the doc under `templates/` (e.g. `memory/<domain>-structure.md`).
- Update `docs/architecture.md` if the program affects first-principle reasoning about the repo.
- Add a changelog entry in `CHANGELOG.md` for the next version draft.

## Copy-paste template

```markdown
# <program-name>

<One or two sentences describing the domain.>

## References

- <convention doc>
- <related program>

## Conventions

- <durable fact about the domain>
- <lifecycle>
- <frontmatter>
- <naming>

## Authority

- <what the agent can do>
- <what it cannot touch>

## Approval gates

- Obvious <thing> -> act.
- Ambiguous <thing> -> surface (in-session: ask; via cron: include in run report).

## Escalation

- <unusual state that halts the program>

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

## Behaviors

### <behavior 1>

1. <step>
2. <step>

### <behavior 2>

1. <step>
2. <step>

## What NOT to do

- Do not <X>.
- Never <Y>.
```
