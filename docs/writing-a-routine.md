# Writing a clawstodian routine

Routines are the scheduled invocations in clawstodian. A routine is a markdown spec under `routines/` that owns the procedure for operating one workspace domain on a schedule.

Routines are **self-contained instructions**. They reference a program for conventions, then carry the full procedure - target, numbered steps, run-report shape. They do NOT describe their schedule or enable state - that information lives in the cron config (set at install time via `INSTALL.md`) and in the human-readable catalog (`templates/crons.md`). A routine spec should read the same whether the cron fires every minute or once a week.

Programs carry conventions; routines carry procedures. A routine references the program for the rules it must obey and then spells out what to do when the cron fires.

## Routine vs program

- **Program** (`programs/<name>.md`) = "this is how we operate this workspace in domain X." Conventions, authority, approval gates, escalation. No procedure.
- **Routine** (`routines/<name>.md`) = "run this procedure when the cron fires." References a program for rules; owns the steps itself.

Before writing a routine, confirm the domain already has a program. If the domain is new, write the program first (see `writing-a-routine.md`'s sibling, `writing-a-program.md`).

## Execution classes

Two classes, distinguished by how the cron's enabled state is managed.

- **Scheduled** - enabled at install, fires on its wall-clock schedule (interval-based `--every` or cron-expression `--cron`), stays enabled. No self-disable. Every firing produces a run-report file and channel post (quiet firings still speak with `outcome: clean` or `no-op`).
- **Heartbeat-toggled burst** - starts disabled. The heartbeat orchestrator enables the cron when a queue exists; the routine self-disables when it drains the queue. Every firing produces both artifacts, including the drain-and-disable firing.

## Anatomy

Canonical section order. All seven routines follow this; stick to it so operators can scan any routine without relearning where to look.

```markdown
# <routine-name> (routine)

<One or two sentences: what this routine does, in terms of the domain it operates on and the program it references.>

## Program

`clawstodian/programs/<program-name>.md` - conventions, authority, approval gates, and escalation.

<Optional second paragraph: one sentence clarifying how this routine relates to the program, or pointing to a convention doc like `memory/daily-note-structure.md`.>

## Target

<What the routine operates on. A specific file path, a selection rule, the full graph, etc.>

<Variants: "Target selection" with numbered steps when picking today's target is non-trivial. "Queue definition" for burst workers that enumerate what is queueable. "Scope" for routines that enumerate dimensions they cover (para-align has six; workspace-clean has five categories of work).>

## <Routine-specific rule sections> (optional)

Rules and definitions that Steps will reference. Example: `sessions-capture` has "Classification rules" and "Turn-level filtering rules" - vocabulary the procedure uses. Keep these above Steps so the reader has the definitions before the procedure that invokes them.

## Steps

Numbered list of what happens in one firing. Subsections (`### Phase 1`, `### Unit-of-work procedure`, `### Trivial-day fast-path` / `### Full seal`) are fine for routines with conditional branches or multi-phase work. Each step starts with a verb.

## Commit

(Optional.) Message template, push policy. Omit when the routine does not commit, or when committing is inline in a numbered step that already spells out the message convention.

## Exec safety

- Run commands by exact path. No `eval`, `bash -c "..."`, or other indirection that hides the real command from the gateway's exec safety layer.
- For multi-line script logic, write the script to `/tmp/clawstodian-<routine>-<context>.py` (or `.sh`) and invoke it by path. Do not inline code via heredoc to an interpreter (`python3 <<EOF ... EOF`); the safety layer blocks that as obfuscation.
- `jq` and `python3 -c '<short expression>'` one-liners are fine when they fit on one line and the intent is obvious.
- Add any routine-specific bans (e.g. git-related forbiddens) as additional bullets.

## Worker discipline

- One pass per firing (or one unit of work per firing for burst routines).
- Discipline rules that apply across the whole procedure: write-first-then-cursor ordering, never-mutate-sealed-notes, read-only-for-detection-steps, etc. NOT procedural content - that lives in Steps.
- Routine-specific prohibitions that go beyond what the program already forbids.

## Self-disable on empty queue

(Burst routines only; omit for Scheduled.) After processing, re-check the queue; if empty:

\`\`\`bash
openclaw cron disable <routine-name>
\`\`\`

**Cron safety: disable means `openclaw cron disable`, NEVER `openclaw cron remove`.**

## Run report

Two artifacts on every firing: a detail file on disk and a multi-line scannable summary delivered to the logs channel by the cron runner. Both follow a shared shape across all routines so the operator does not need to learn a new format per routine.

### File on disk

Write to `memory/runs/<routine-name>/<YYYY-MM-DD>T<HH-MM-SS>Z.md` (UTC, colons replaced with hyphens so the filename is filesystem-safe and sorts chronologically). File shape:

\`\`\`markdown
# <routine-name> run report

- timestamp: 2026-04-18T12:30:00Z
- context: <date | ISO-week | timestamp>     # routine's unit identifier
- outcome: <sealed|processed|committed|tidied|skipped|failed|...>  # routine-specific enum
- path: <alternate code path if any, e.g. "full" / "trivial-day-fast-path" for seal>
- cron_state: <enabled|disabled> -> <enabled|disabled>  # omit line for Scheduled

## What happened

<Routine-specific subsections. One subsection per concern (admission, capture, merge,
curate, etc.). Inside each: short bullets with counts and names.>

## Queue after firing

<Routine-relevant queue state + cron-state-after. Use "n/a" or omit the section for
Scheduled routines that do not track a queue.>

## Commits

<Each commit this firing produced: short hash + subject. "(none)" if the routine does
not commit or the tree was clean.>

## Surfaced for operator

<Things the routine flagged for operator judgment instead of acting on. Bullets.
"(none)" if nothing needed surfacing.>

## Channel summary

<The exact multi-line text posted to the channel, for self-containment.>
\`\`\`

Drop any section that is stably `(none)` for this routine (e.g. `para-align` never has a Queue section; `workspace-clean` never commits, so its Commits section is stably "(none)"). Keep the skeleton for sections that could in principle have content.

### Channel summary format

Multi-line, one insight per line. Scannable. Shared shape across routines:

\`\`\`
<routine-name> · <context> · <outcome or path>
<primary insight line>
<secondary insight line(s)>
Queue: <queue state> · cron: <enabled|disabled>      # omit for Scheduled
Report: memory/runs/<routine-name>/<ts>.md
\`\`\`

Conventions:

- Line 1 is the header: name · context · categorical outcome. Dots (`·`) as field separators so the header reads left-to-right like "what · when · result".
- Middle lines carry the news. One primary concern per line; group tightly-related secondary counts on the same line separated by `·`.
- The Queue line appears only for burst routines that track a queue (`sessions-capture`, `daily-seal`, `para-extract`). Drop it for Scheduled routines (`workspace-clean`, `git-clean`, `para-align`).
- The Report line is always last. Relative path from workspace root so it clicks or copies cleanly.

### Every firing produces both artifacts

No `NO_REPLY`. Every cron firing writes a run-report file and posts a channel summary, even when the routine had nothing to do. The fact that the cron fired is itself information - the operator needs to know the cron ran, not infer it from silence.

Quiet firings get an `outcome: no-op` (or an equivalent routine-specific term like `clean`) and a short 3-line channel post: header line, one line of "nothing to do", Report pointer. Files on disk stay terse too.

This catches silent-failure modes that NO_REPLY would have hidden: cron not firing at all, heartbeat not toggling it on, visibility config clobbered. Every healthy firing produces evidence in the channel and on disk.
```

That is all. No `## Install`, no `## Verify`, no `## Uninstall` - those live in the top-level docs.

## What a routine must NOT carry

- **No schedule.** No "every 30m", "every 2h", "Sunday 06:00", or "while enabled" framing. The cron configuration owns cadence; if the operator reconfigures the cron, the routine spec should not have to change.
- **No install command.** `openclaw cron add` invocations live in `INSTALL.md` under "Cron install commands". Each routine has its line there; the routine spec does not.
- **No verify / uninstall commands.** `VERIFY.md` and `UNINSTALL.md` handle those.
- **No historical notes.** The changelog is the changelog. Routines describe the present, not what was replaced.
- **No rationale for the overall system shape.** `docs/architecture.md` explains the system; programs explain their domains. Brief rationale for a specific step is fine where it clarifies the procedure; anything longer belongs in the program or architecture doc.

## Install command conventions

Install commands live in `INSTALL.md` under "Cron install commands", not in the routine spec. Each command follows the same shape:

- **`--name`** matches the spec filename minus `.md`.
- **`--every <interval>`** for interval-based routines. **`--cron "<expr>"`** for wall-clock-bound schedules. Never both.
- **`--disabled`** on heartbeat-toggled bursts only. Omit for Scheduled.
- **`--session isolated`** always. Do not use `--session current` - it captures an ephemeral session key that drifts.
- **`--light-context`** always. Bootstrap files are not needed; the routine reads its spec (and the program it references) on demand.
- **`--timeout-seconds <n>`** always, sized to the routine's workload. The OpenClaw `--timeout` default (30s) fails every agent-driven routine. Pick a ceiling generous enough to absorb the worst real firing; see `docs/crons-config.md` > "Timeouts" for current per-routine values and rationale.
- **`--announce --channel --to`** routes the run report to the notifications channel. Substitute `--no-deliver` if the operator prefers silent runs.
- **`--message`** is always `"Read clawstodian/routines/<name>.md and execute."`

For maintenance crons, **do not set a sessionKey**. `--session isolated` alone produces a session-store entry named `agent:<agentId>:cron:<jobId>` automatically. Isolated per job, stable across runs, no conversation context inherited.

Clawstodian deliberately does NOT set `--thinking`, `--model`, `--tz`, `--stagger`, or `--best-effort-deliver` in install commands - those are operator judgment calls after install. See `docs/crons-config.md` > "Flags clawstodian deliberately does NOT set" for why.

## Catalog integration

When you ship a new routine:

- Confirm the program for the domain exists. If not, write the program first (see `writing-a-program.md`).
- Add the routine to the Routines catalog in `templates/AGENTS.md` under the right execution class. Name its schedule and enable behavior there.
- Add an entry to `templates/crons.md` with schedule, enable logic, and the program it invokes.
- Add the `openclaw cron add` command to `INSTALL.md` under "Cron install commands".
- Add the cron name to the `VERIFY.md` registration check and the `UNINSTALL.md` cron removal loop.
- If the routine is heartbeat-toggled, add or update the enable/disable logic in `templates/HEARTBEAT.md`.
- Add a changelog entry in `CHANGELOG.md` for the next version draft.
