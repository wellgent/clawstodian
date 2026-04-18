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

- **Always-on cron** - enabled at install. Fires on its schedule regardless of workspace state. Every firing produces a run-report file and channel post (quiet firings still speak). No self-disable section in the routine.
- **Fixed cron** - enabled at install, wall-clock schedule. Usually carries meaningful state on every run. Every firing produces both artifacts. No self-disable section.
- **Heartbeat-toggled burst** - starts disabled. The heartbeat orchestrator enables the cron when a queue exists and disables it when empty. The routine self-disables when it drains the queue. Every firing produces both artifacts, including the drain-and-disable firing.

## Anatomy

```markdown
# <routine-name> (routine)

<One sentence: what this routine does, in terms of the program behavior it invokes.>

## Program

`clawstodian/programs/<program-name>.md` - follow the "<behavior>" behavior.

## Target

<What the routine operates on. A specific file, a selection rule, the full graph, etc.>

## Exec safety

- Run commands by exact path. No `eval`, `bash -c "..."`, or other indirection that hides the real command from the gateway's exec safety layer.
- For multi-line script logic, write the script to `/tmp/clawstodian-<routine>-<context>.py` (or `.sh`) and invoke it by path. Do not inline code via heredoc to an interpreter; the safety layer blocks that as obfuscation.
- `jq` and `python3 -c '<short expression>'` one-liners are fine when they fit on one line and the intent is obvious.
- Add any routine-specific bans (e.g. git-hygiene forbids `--no-verify` and `git reset --hard`) above the generic block.

## Worker discipline

- One pass per firing.
- <Other discipline specific to this routine.>

## Self-disable on empty queue

(Burst workers only; omit for always-on and fixed crons.) After processing, re-check the queue; if empty:

\`\`\`bash
openclaw cron disable <routine-name>
\`\`\`

## Run report

Two artifacts on meaningful firings: a detail file on disk and a multi-line scannable summary delivered to the logs channel by the cron runner. Both follow a shared shape across all routines so the operator does not need to learn a new format per routine.

### File on disk

Write to `memory/runs/<routine-name>/<YYYY-MM-DD>T<HH-MM-SS>Z.md` (UTC, colons replaced with hyphens so the filename is filesystem-safe and sorts chronologically). File shape:

\`\`\`markdown
# <routine-name> run report

- timestamp: 2026-04-18T12:30:00Z
- context: <date | ISO-week | timestamp>     # routine's unit identifier
- outcome: <sealed|processed|committed|tidied|skipped|failed|...>  # routine-specific enum
- path: <alternate code path if any, e.g. "full" / "trivial-day-fast-path" for seal>
- cron_state: <enabled|disabled> → <enabled|disabled>  # omit line for always-on and fixed crons

## What happened

<Routine-specific subsections. One subsection per concern (admission, capture, merge,
curate, etc.). Inside each: short bullets with counts and names.>

## Queue after firing

<routine-relevant queue state + cron-state-after. Use "n/a (always-on)" or "n/a (fixed cron)"
when not applicable.>

## Commits

<Each commit this firing produced: short hash + subject. "(none)" if the routine does
not commit or the tree was clean.>

## Surfaced for operator

<Things the routine flagged for operator judgment instead of acting on. Bullets.
"(none)" if nothing needed surfacing.>

## Channel summary

<The exact multi-line text posted to the channel, for self-containment.>
\`\`\`

Drop any section that is genuinely `(none)` *and* stably so for this routine (e.g. `para-align` never commits, so it does not need the `Commits` section at all). Keep the five-section skeleton whenever the section could in principle have content.

### Channel summary format

Multi-line, one insight per line. Scannable. Shared shape across routines:

\`\`\`
<routine-name> · <context> · <outcome or path>
<primary insight line>
<secondary insight line(s)>
Queue: <queue state> · cron: <enabled|disabled>      # omit for always-on and fixed crons
Report: memory/runs/<routine-name>/<ts>.md
\`\`\`

Conventions:

- Line 1 is the header: name · context · categorical outcome. Dots (`·`) as field separators so the header reads left-to-right like "what · when · result".
- Middle lines carry the news. One primary concern per line; group tightly-related secondary counts on the same line separated by `·`.
- The Queue line appears only for burst workers that track a queue (`capture-sessions`, `seal-past-days`, `para-extract`). Drop it for `workspace-tidy`, `git-hygiene`, `para-align`.
- The Report line is always last. Relative path from workspace root so it clicks or copies cleanly.

### Every firing produces both artifacts

No `NO_REPLY`. Every cron firing writes a run-report file and posts a channel summary, even when the routine had nothing to do. The fact that the cron fired is itself information - the operator needs to know the cron ran, not infer it from silence.

Quiet firings get an `outcome: no-op` (or equivalent routine-specific term like `clean`) and a short 3-line channel post: header line, one line of "nothing to do", Report pointer. Files on disk stay terse too.

This catches silent-failure modes that NO_REPLY would have hidden: cron not firing at all, heartbeat not toggling it on, visibility config clobbered. Every healthy firing produces evidence in the channel and on disk.
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
capture-sessions · 2026-04-18T12:30Z · captured
Admitted: 3 (skipped=2, interactive=1)
Captured: 1 session · dates: 2026-04-18
Bleed: 0 · slugs merged: 0 · insights filed: 0
Queue: un-admitted=0 · stale=0 · cron: enabled
Report: memory/runs/capture-sessions/2026-04-18T12-30-00Z.md
```

```
seal-past-days · 2026-04-17 · sealed (full)
Sections: 7 → 5 · noise blocks removed: 2 · slugs merged: 0
Frontmatter: topics=5 · people=2 · projects=3
Commit: abc1234 memory: seal 2026-04-17 - VPS migration
Queue: 2 notes remaining · cron: enabled
Report: memory/runs/seal-past-days/2026-04-18T02-30-00Z.md
```

```
para-align · 2026-W16 · fixes-applied
Verified: 48 entities (clean=47, violations=1)
Trivial fixes: 3 applied
Proposals: 1 awaiting operator
Report: memory/runs/para-align/2026-04-20T06-00-00Z.md
```

Keep reports greppable line-by-line. Prose belongs elsewhere.

## Every firing speaks

Every routine firing produces a channel post and a run-report file. No silent firings. A routine that "had nothing to do" still announces `no-op` (or `clean`, etc.) so the operator sees the cron is alive. Silence belongs to truly-disabled crons and to operator-judgment ticks (heartbeat outside active hours), not to busy workers doing nothing.

This is a change from the earlier `NO_REPLY` convention, which hid failures: a routine returning `NO_REPLY` could mean "clean" or "dead", and the operator could not tell from the channel alone. Always-speaking routines close that gap.

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
