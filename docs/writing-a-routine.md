# Writing a clawstodian routine

Routines are the scheduled invocations in clawstodian. A routine is a markdown spec under `routines/` that dispatches a behavior from a program at a specific cadence.

Routines are thin. They reference a program, pick a behavior, define a target and a run report, and register a cron job. The behavior's steps live in the program; the routine does not duplicate them. See `writing-a-program.md` for writing programs.

## Routine vs program

- **Program** (`programs/<name>.md`) = "this is how we operate this workspace in domain X." The authority.
- **Routine** (`routines/<name>.md`) = "run this instruction set at this cadence." The invocation.

Before writing a routine, confirm the behavior you want to schedule already exists in a program. If it does not, write the program first.

## Execution classes

Two classes, distinguished by how the cron's enabled state is managed:

- **Always-on cron** - enabled at install time. Fires on its schedule regardless of workspace state. Quiet runs return `NO_REPLY` and stay silent.
- **Heartbeat-toggled burst** - starts disabled. The heartbeat orchestrator enables the cron when a queue exists and disables it when empty. Fires every 30m while enabled. The routine itself disables its own cron when it drains the queue to empty.

Neither class changes what the routine does; it changes how the cron's enabled state is managed.

## Anatomy

```markdown
# <routine-name> (routine)

<Schedule + enable state.> Invokes <program>: <behavior>.

## Program

`clawstodian/programs/<program-name>.md` - follow the "<behavior>" behavior.

## Target

<What the routine operates on. A specific file, a selection rule, the full graph, etc.>

## Exec safety

<If the routine uses shell.>

## Worker discipline

- One pass per firing.
- <Other discipline specific to this routine.>

## Self-disable on empty queue

(Burst workers only.) After processing, check the queue; if empty, `openclaw cron disable <routine-name>`.

## Run report

Single line delivered to the logs channel by the cron runner:

\`\`\`
<routine-name> <context>: <fields separated by pipes>
\`\`\`

Return `NO_REPLY` on no-change runs so quiet ticks stay silent. (Only applies when quiet runs are meaningful; some routines always report.)

## Install

\`\`\`bash
openclaw cron add \
  --name <routine-name> \
  --every 30m | --cron "<expr>" \
  [--disabled] \
  --session isolated \
  --light-context \
  --announce --channel <channel> --to "channel:<your-logs-channel-id>" \
  --message "Read clawstodian/routines/<routine-name>.md and execute."
\`\`\`

## Verify

\`\`\`bash
openclaw cron list [--all] | grep <routine-name>
\`\`\`

## Uninstall

\`\`\`bash
openclaw cron remove <routine-name>
\`\`\`
```

## Install command conventions

Every routine's install command follows the same shape:

- **`--name`** matches the spec filename minus `.md`.
- **`--every <interval>`** for interval-based routines. **`--cron "<expr>"`** for wall-clock-bound schedules. Never both.
- **`--disabled`** on heartbeat-toggled bursts only. Omit for always-on crons.
- **`--session isolated`** always. Do not use `--session current` - it captures an ephemeral session key that drifts.
- **`--light-context`** always. Bootstrap files are not needed; the routine reads its spec (and the program it references) on demand.
- **`--announce --channel --to`** routes the run report to the operator's maintainer logs channel. Substitute `--no-deliver` if the operator prefers silent runs.
- **`--message`** is always `"Read clawstodian/routines/<name>.md and execute."`

## Run report conventions

Every routine's run report is a single line. Fields are pipe-separated. The cron runner delivers the line to the logs channel as one message.

Shape:

```
<routine-name> <context>: <action> | <counts> | <queue> | <cron state>
```

Examples:

```
daily-note 2026-04-18: appended 3 sections | merged 1 slug sibling | filed 0 insights | 0 awaiting operator
seal-past-days 2026-04-15: sealed | sections 7->5 | para_status: pending | queue: 2 | cron: enabled
para-align 2026-W16: verified 48 entities | trivial fixes 3 | proposals 1 (awaiting operator)
```

Keep reports greppable and scan-friendly. Prose belongs elsewhere.

## NO_REPLY convention

Routines where a quiet run is common (daily-note with no new activity, git-hygiene with a clean tree) should return `NO_REPLY` on no-change. The cron runner interprets `NO_REPLY` as "suppress delivery" - the channel stays silent.

Routines where every run carries meaningful state transition (seal-past-days succeeded, para-extract processed a note, para-align verified the weekly graph) should always report. Do not `NO_REPLY` a successful operation just because the counts are low.

## Sessions: what to pass and what to leave alone

For maintenance crons, **do not set a sessionKey**. `--session isolated` alone produces a session-store entry named `agent:<agentId>:cron:<jobId>` automatically. Isolated per job, stable across runs, no conversation context inherited.

Rule of thumb: if you did not deliberately choose to tie a cron to a specific conversation, the sessionKey should be empty.

## Catalog integration

When you ship a new routine:

- Confirm the behavior exists in a program. If not, write the program first (see `writing-a-program.md`).
- Add the routine to `AGENTS-SECTION.md` Routines catalog under the right execution class.
- Add an entry to `templates/crons.md` with schedule, enable logic, and the program/behavior it invokes.
- Add the `openclaw cron add` command in the routine spec itself (the canonical install location).
- Update `INSTALL_FOR_AGENTS.md`'s smoke-test name list.
- If the routine is heartbeat-toggled, add or update the enable/disable logic in `HEARTBEAT-SECTION.md`.
- Add a changelog entry in `CHANGELOG.md` for the next version draft.
