# Writing a clawstodian routine

Routines are the unit of work in clawstodian. A routine is a markdown spec under `routines/` that defines a named, scoped, repeatable chunk of workspace maintenance.

Routines are context-agnostic behavioral specs. They describe what to do, not when or how to schedule it. An agent can follow a routine through a scheduled cron dispatch or during a normal session when the need arises. Scheduling, cron commands, enable logic, and delivery wiring live centrally in `INSTALL_FOR_AGENTS.md`.

## What belongs in a routine

A routine spec answers these questions in order:

1. What does this routine do?
2. What files, tools, and actions is it allowed to use?
3. When does it need operator approval vs. when does it act?
4. What unusual states should it surface instead of handling?
5. How does it execute shell safely?
6. What are the steps?
7. What must it never do?
8. How does it report when something changes?

That is the whole anatomy. No cron cadence. No install blocks. No verify commands.

## Anatomy

```markdown
# <routine-name>

<One or two sentences: what this routine does. Behavioral, not scheduled.>

## References

- <convention doc>
- <related routine>

## Authority

- What the routine is permitted to do.
- What it must not touch.

## Approval gates

- <obvious action -> act>
- <ambiguous action -> surface in the summary>

## Escalation

<Unusual states that halt the routine and appear in the summary.>

## Exec safety

<If the routine uses shell. Usually: run by exact path, no heredocs.>

## What to do

1. <step one>
2. <step two>

## What NOT to do

- <prohibition>

## Summary

<Format for the one-line report when something changed. Include the NO_REPLY convention for cron-driven silent runs.>
```

Routines that drain a queue (burst workers like `seal-past-days` and `para-extract`) include the self-disable step in their "What to do" or "After processing" section. The step runs `openclaw cron disable <name>` when the queue is empty and was invoked via cron. In-session manual invocations ignore that step.

Routines that commit include a `Commit` section with the commit-message convention.

## Summary section conventions

Every routine has a Summary section. It defines:

- The one-line shape the routine produces when something changed.
- The silence convention for quiet runs: produce no summary. When dispatched by cron, return `NO_REPLY` so the run stays silent in the logs channel.

The format should be greppable and scan-friendly. Pipe-separated fields beat prose. Examples:

```
daily-note 2026-04-18: appended 3 sections | merged 1 slug sibling | filed 0 insights | 0 awaiting operator
```

```
git-hygiene: 2 commits pushed | 0 awaiting operator decision
```

Under cron dispatch, the runner announces the summary to the operator's logs channel. Under in-session invocation, the agent incorporates the same information into its normal reply flow.

## Cron wiring

Every routine runs on cron by default. Scheduling decisions (cadence, enable logic, schedule expression) and the exact `openclaw cron add` commands live in `INSTALL_FOR_AGENTS.md` under "Cron install commands", in `templates/crons.md` as the workspace dashboard, and in `AGENTS-SECTION.md` as the catalog.

This separation means:

- Routines stay portable - an agent can follow one outside any specific cron context.
- Scheduling can change without editing every spec.
- The install flow has a single source of truth for cron registration.

Two execution classes exist at the orchestration layer:

- **Always-on cron** - registered enabled; fires on its schedule; quiet runs return `NO_REPLY`.
- **Heartbeat-toggled burst** - registered disabled; the heartbeat orchestrator enables when a queue exists and disables when empty; the routine itself disables its cron when it drains the queue.

Neither class changes the routine's behavior. The class is orchestration context, documented in `AGENTS-SECTION.md`.

## Adding a new routine

When you ship a new routine:

1. Write the spec in `routines/<name>.md` following the anatomy.
2. Add the routine to the `AGENTS-SECTION.md` catalog under the right class with a one-line description.
3. Add an entry to `templates/crons.md` with schedule and enable logic for the workspace dashboard.
4. Add the `openclaw cron add` command to `INSTALL_FOR_AGENTS.md` under "Cron install commands" and add the routine name to the smoke-test name list.
5. If it is a burst worker, reference it from `HEARTBEAT-SECTION.md` where the orchestrator decides to enable or disable it.
6. Add a changelog entry in `CHANGELOG.md` for the next version draft.

The routine spec stays focused on behavior. Everything about wiring lives in the catalog and the install flow.

## Copy-paste template

```markdown
# <routine-name>

<What this routine does, in one or two sentences. Behavioral, not scheduled.>

## References

- <convention doc>
- <related routine>

## Authority

- <what it can do>
- <what it cannot touch>

## Approval gates

- <obvious -> act>
- <ambiguous -> surface in the summary>

## Escalation

<Unusual states that halt the routine.>

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

## What to do

1. <step one>
2. <step two>
3. <step three>

## What NOT to do

- Never <X>.
- Do not <Y>.

## Summary

When something changed, report one line:

\`\`\`
<routine-name>: <fields separated by pipes>
\`\`\`

When nothing changed, produce no summary. Under cron dispatch, return `NO_REPLY`.
```
