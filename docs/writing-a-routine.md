# Writing a clawstodian routine

Routines are the scheduled invocations in clawstodian. A routine is a markdown spec under `routines/` that dispatches a behavior from a program.

Routines are **pure instructions**. They reference a program, pick a behavior, define a target, worker discipline, and a run report. They do NOT describe their schedule or enable state - that information lives in the cron config (set at install time via `INSTALL.md`) and in the human-readable catalog (`templates/crons.md`). A routine spec should read the same whether the cron fires every minute or once a week.

Behavior steps live in the program; the routine does not duplicate them. See `writing-a-program.md` for writing programs.

## Routine vs program

- **Program** (`programs/<name>.md`) = "this is how we operate this workspace in domain X." The authority.
- **Routine** (`routines/<name>.md`) = "these are the instructions the agent follows when this cron fires." The invocation.

Before writing a routine, confirm the behavior you want to schedule already exists in a program. If it does not, write the program first.

## Execution classes

Three classes, distinguished by how the cron's enabled state is managed. The class is a property of the cron configuration, not the routine spec - but the routine's `Self-disable` section (if any) depends on the class, so the spec has to know which one it is.

- **Always-on cron** - enabled at install. Fires on its schedule regardless of workspace state. Quiet runs return `NO_REPLY` and stay silent. No self-disable section in the routine.
- **Fixed cron** - enabled at install, wall-clock schedule. Usually carries meaningful state on every run, so the routine always reports (no `NO_REPLY`). No self-disable section.
- **Heartbeat-toggled burst** - starts disabled. The heartbeat orchestrator enables the cron when a queue exists and disables it when empty. The routine self-disables when it drains the queue.

## Anatomy

```markdown
# <routine-name> (routine)

<One sentence: what this routine does, in terms of the program behavior it invokes.>

## Program

`clawstodian/programs/<program-name>.md` - follow the "<behavior>" behavior.

## Target

<What the routine operates on. A specific file, a selection rule, the full graph, etc.>

## Exec safety

<If the routine uses shell. Commands by exact path, no heredoc-to-shell piping, etc.>

## Worker discipline

- One pass per firing.
- <Other discipline specific to this routine.>

## Self-disable on empty queue

(Burst workers only; omit for always-on and fixed crons.) After processing, re-check the queue; if empty:

\`\`\`bash
openclaw cron disable <routine-name>
\`\`\`

## Run report

Single line delivered to the logs channel by the cron runner:

\`\`\`
<routine-name> <context>: <fields separated by pipes>
\`\`\`

<When to return NO_REPLY, if applicable.>
```

That is all. No `## Install`, no `## Verify`, no `## Uninstall` - those live in the top-level docs.

## What a routine must NOT carry

- **No schedule.** No "every 30m", "every 2h", "Sunday 06:00", or "while enabled" framing. The cron configuration owns cadence; if the operator reconfigures the cron, the routine spec should not have to change.
- **No install command.** `openclaw cron add` invocations live in `INSTALL.md` under "Cron install commands". Each routine has its line there; the routine spec does not.
- **No verify / uninstall commands.** `VERIFY.md` and `UNINSTALL.md` handle those.
- **No historical notes.** The changelog is the changelog. Routines describe the present, not what was replaced.
- **No rationale or design motivation.** The program explains *why*; `docs/architecture.md` explains the system shape. The routine says *what* the agent does when the cron fires.

## Run report conventions

Every routine's run report is a single line. Fields are pipe-separated. The cron runner delivers the line to the logs channel as one message.

Shape:

```
<routine-name> <context>: <action> | <counts> | <queue> | <cron state>
```

Examples:

```
capture-sessions 96a0c068: captured | classification: interactive | lines: 142->189 | dates: [2026-04-18] | merged 1 slugs | filed 0 insights | bleed 0 sealed | queue: un-admitted=2/stale=0 | cron: enabled
seal-past-days 2026-04-15: sealed | sections 7->5 | para_status: pending | queue: 2 | cron: enabled
para-align 2026-W16: verified 48 entities | trivial fixes 3 | proposals 1 (awaiting operator)
```

Keep reports greppable and scan-friendly. Prose belongs elsewhere.

## NO_REPLY convention

Routines where a quiet run is common (git-hygiene with a clean tree, capture-sessions on a skipped-classification admission) should return `NO_REPLY` on no-change. The cron runner interprets `NO_REPLY` as "suppress delivery" - the channel stays silent.

Routines where every run carries meaningful state transition (seal-past-days succeeded, para-extract processed a note, para-align verified the weekly graph) should always report. Do not `NO_REPLY` a successful operation just because the counts are low.

## Install command conventions

Install commands live in `INSTALL.md` under "Cron install commands", not in the routine spec. Each command follows the same shape:

- **`--name`** matches the spec filename minus `.md`.
- **`--every <interval>`** for interval-based routines. **`--cron "<expr>"`** for wall-clock-bound schedules. Never both.
- **`--disabled`** on heartbeat-toggled bursts only. Omit for always-on and fixed crons.
- **`--session isolated`** always. Do not use `--session current` - it captures an ephemeral session key that drifts.
- **`--light-context`** always. Bootstrap files are not needed; the routine reads its spec (and the program it references) on demand.
- **`--announce --channel --to`** routes the run report to the notifications channel. Substitute `--no-deliver` if the operator prefers silent runs.
- **`--message`** is always `"Read clawstodian/routines/<name>.md and execute."`

For maintenance crons, **do not set a sessionKey**. `--session isolated` alone produces a session-store entry named `agent:<agentId>:cron:<jobId>` automatically. Isolated per job, stable across runs, no conversation context inherited.

## Catalog integration

When you ship a new routine:

- Confirm the behavior exists in a program. If not, write the program first (see `writing-a-program.md`).
- Add the routine to the Routines catalog in `templates/AGENTS.md` under the right execution class. Name its schedule and enable behavior there.
- Add an entry to `templates/crons.md` with schedule, enable logic, and the program/behavior it invokes. This is where the operator looks up cadence.
- Add the `openclaw cron add` command to `INSTALL.md` under "Cron install commands".
- Add the cron name to the `VERIFY.md` registration check and the `UNINSTALL.md` cron removal loop.
- If the routine is heartbeat-toggled, add or update the enable/disable logic in `templates/HEARTBEAT.md`.
- Add a changelog entry in `CHANGELOG.md` for the next version draft.
