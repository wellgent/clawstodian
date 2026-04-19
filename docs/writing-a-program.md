# Writing a clawstodian program

Programs are the unit of authority in clawstodian. A program is a markdown spec under `programs/` that describes how a workspace domain is governed - conventions, authority, approval gates, escalation rules, and what to never do.

Programs are read by agents at session bootstrap (via `AGENTS.md`) so in-session agents know how each domain is operated. Routines under `routines/` dispatch these same conventions from cron; see `writing-a-routine.md` for how routines pair with programs.

## Program vs routine

The distinction is **what** vs **when**.

- **Program**: "this is how we operate this workspace in domain X." Domain-shaped, time-agnostic. Contains conventions, authority, approval gates, escalation, and what-NOT-to-do. Read at bootstrap by every agent. Changes only when the convention itself evolves.
- **Routine**: "run this procedure at this cadence." Schedule-shaped. Contains target, numbered steps, worker discipline, run report. Read only inside cron dispatch. Multiple routines can reference the same program.

Programs carry conventions; **routines carry procedures**. A program should not embed numbered steps or named behaviors - those belong in the routines that dispatch the domain, so the program stays time-agnostic and the procedural detail lives where it actually runs.

Before writing a program, ask: is this a new domain the workspace operates in, or a new procedure inside an existing domain? New domain -> program. New procedure -> see `writing-a-routine.md`.

## Anatomy

Every program uses the same section order. Agents read top-to-bottom to understand the domain. Section order is canonical; stick to it.

```markdown
# <program-name>

<One or two sentences describing the domain this program governs.>

## Who <verb>

Who primarily does the work in this domain and what the cron backstop catches. One short paragraph, maybe two. The verb matches the domain - `writes` (daily-notes), `tends` (workspace), `commits` (repo), `writes and maintains` (para).

## References

- Convention docs this program relies on (e.g. `memory/daily-note-structure.md`).
- Related programs.

## Conventions

Durable facts about this domain: file naming, lifecycle states, frontmatter, directory structure, any invariants the agent must respect. Bullets, not paragraphs.

## Authority

What the agent is permitted to do in this domain. Close with a "Must NOT ..." sentence that names the domain-level prohibitions an operator would want enforced.

## Approval gates

Which actions are obvious (just act) vs ambiguous (surface for operator). "Surface" means: in-session - ask the operator in chat; via cron - include in the routine's run report.

## Escalation

Unusual states that halt the agent's work in this domain and surface for operator judgment.

## What NOT to do

Prohibitions specific to this program. Some may overlap with the Must-NOT line in Authority; that is fine - restate the load-bearing prohibitions here as a quick scannable list.
```

The program contains no numbered steps. Any procedure belongs in a routine.

## What programs do NOT carry

- **No numbered procedures or named behaviors.** Procedures live in routines. A program defines convention and authority; routines apply both to execute specific operations.
- **No schedules, cadences, or enable/disable logic.** That is routine territory.
- **No exec-safety rules for shell commands.** Shell discipline lives on the routine that runs shell; in-session agents follow their host's safety rules.
- **No run-report formats.** Reports are per-firing artifacts tied to a schedule - routine territory.
- **No install or verify commands.** Those live in `INSTALL.md` and `VERIFY.md`.

## Approval gate and escalation language

Programs support two invocation contexts: in-session (agent is working with the user) and cron-dispatched (isolated session, no user). The language should work for both.

- "Obvious placement -> act." Applies everywhere.
- "Ambiguous placement -> surface." In-session: ask the operator in chat. Via cron: include in the routine's run report so the operator sees it in the logs channel.

Use "surface" rather than "ask" throughout; clarify the context distinction once at the top of Approval gates if useful.

## Catalog integration

When you ship a new program:

- Add it to the Programs catalog in `templates/AGENTS.md` with a one-sentence domain description.
- If a routine needs to dispatch procedure inside this domain, add or update the relevant `routines/<name>.md`. The routine carries the procedure.
- If this program introduces new conventions that reference docs, update or add the doc under `templates/` (e.g. `memory/<domain>-structure.md`).
- Update `docs/architecture.md` if the program affects first-principle reasoning about the repo.
- Add a changelog entry in `CHANGELOG.md` for the next version draft.

## Copy-paste template

```markdown
# <program-name>

<One or two sentences describing the domain.>

## Who <verb>

**In-session agents are the primary <verb>s.** <What they do during a session, when the situation in this domain arises.> This is the default path.

Under cron, <routine-name(s)> <brief description of the backstop role>.

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

Must NOT <major prohibition>.

## Approval gates

- **Obvious <thing> -> act.**
- **Ambiguous <thing> -> surface** (in-session: ask; via cron: include in run report).

## Escalation

- <unusual state that halts the agent and surfaces for operator judgment>

## What NOT to do

- Do not <X>.
- Never <Y>.
```
