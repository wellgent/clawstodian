# Writing a clawstodian routine

Routines are the unit of work in clawstodian. A routine is a markdown spec under `routines/` that defines a named, scoped, repeatable chunk of workspace maintenance. Every routine runs as its own cron job. This guide is for anyone extending the package - adding a new always-on cron, a new heartbeat-toggled burst worker, or a new fixed-schedule job.

## Pick the pattern first

| Class | Trigger | Schedule | Use when |
| --- | --- | --- | --- |
| **Always-on cron** | Cron, enabled by default | `--every 30m` or `--cron "<expr>"` | The work is cheap, frequent, and self-judging (nothing to do → `NO_REPLY`) |
| **Heartbeat-toggled burst** | Cron, starts disabled; heartbeat toggles | `--every 30m` while enabled | A queue accumulates and needs draining; heartbeat enables on demand |

Preference: always-on cron beats heartbeat-toggled burst. Use burst only when the work is queue-shaped and the queue is frequently empty (so keeping the cron enabled would waste budget).

The heartbeat orchestrator never executes routines. It only reads state, toggles burst workers, spot-checks health, and posts an executive summary.

## Anatomy

Every routine uses the same anatomy. Section order matters - operators read top-to-bottom to understand the routine.

```markdown
# <routine-name>

One-sentence description with the class (e.g. "Always-on cron: keep today's canonical note current.").

## References

- Convention docs this routine relies on (e.g. `memory/daily-note-structure.md`).
- Companion routines (e.g. "Burst worker for past days -> `clawstodian/routines/seal-past-days.md`").

## Authority

What the routine is permitted to do. Tools it uses. Files it creates, reads, or edits. What it must not touch. If the routine toggles its own cron (burst workers), say so here.

## Trigger

The cron schedule and, for bursts, the enable/disable logic.

## Approval gates

Which actions need operator confirmation, which do not. One or two short bullets.

## Escalation

Which unusual states should be surfaced via the reply rather than acted on. Name them explicitly.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

## What to do

Numbered steps. Explicit, specific, ordered.

## What NOT to do

Bullet list of prohibitions. "Never X" / "Do not Y".

## Reply

Single-line announce format the runner posts to the logs channel. Include a `NO_REPLY` shape for quiet runs where nothing changed.

## Install

<install block - see conventions below>

## Verify

<verification command>

## Uninstall (optional)

<uninstall command, typically `openclaw cron remove <name>`>
```

All routines have Install and Verify - there are no heartbeat-direct routines in v0.4.

## Install command conventions

Every routine's install command follows the same shape:

```bash
openclaw cron add \
  --name <routine-name> \              # matches spec filename without .md
  --every 30m | --cron "<expr>" \      # schedule (pick one)
  [--disabled] \                       # heartbeat-toggled bursts only
  --session isolated \                 # always isolated for maintenance
  --light-context \                    # always; the spec loads what it needs
  --announce --channel <channel> --to "channel:<your-logs-channel-id>" \
  --message "Read clawstodian/routines/<routine-name>.md and execute."
```

Flag notes:

- **`--name`** matches the spec filename minus `.md`. That name is how `memory/crons.md`, the heartbeat orchestrator, and operators refer to the job.
- **`--every`** for interval-based routines. **`--cron`** for wall-clock-bound schedules. Never both.
- **`--disabled`** on heartbeat-toggled bursts only. Heartbeat enables on demand. Omit for always-on crons.
- **`--session isolated`** always for maintenance crons. Do not use `--session current` - it captures an ephemeral TUI or DM session key that drifts and orphans cron-session entries over time.
- **`--light-context`** always. Bootstrap files are not needed; the spec loads what it needs.
- **`--announce --channel --to`** routes summaries to the operator's maintainer logs channel. Substitute `--no-deliver` if the operator explicitly wants silent runs.
- **`--message`** is always `"Read clawstodian/routines/<name>.md and execute."` The spec is the authority; the cron payload is just the dispatch.

## Sessions: what to pass and what to leave alone

For maintenance crons, **do not set a sessionKey**. `--session isolated` alone produces a session-store entry named `agent:<agentId>:cron:<jobId>` automatically. Isolated per job, stable across runs, no conversation context inherited.

Rule of thumb: if you did not deliberately choose to tie a cron to a specific conversation, the sessionKey should be empty.

## Delivery: announce by default, `NO_REPLY` for quiet runs

The runner owns the final delivery path for isolated crons. Whatever plain-text summary the agent returns becomes the announcement. If the agent returns `NO_REPLY` or an empty reply, delivery is suppressed automatically.

Design the routine's `What to do` so that steady-state-quiet paths cleanly return `NO_REPLY`. A well-designed always-on cron produces channel noise only when it actually changed something.

Do NOT rely on `--no-deliver` at the cron level to "make the routine quiet"; that hides real events. Let the routine's reply shape determine noise.

## Heartbeat toggling (burst workers only)

If your routine is a burst worker, the heartbeat orchestrator enables and disables the cron based on queue state. In the spec, document:

1. The exact queue definition - what files or state qualify as "queued."
2. The `openclaw cron disable <name>` call the routine itself makes when it drains the queue to empty.

The heartbeat's corresponding logic (the condition under which it re-enables the cron) belongs in `HEARTBEAT-SECTION.md`, not in the routine spec. Reference it from the routine's Trigger section so readers know which side is doing what.

## Catalog integration

When you ship a new routine:

- Add the routine to `AGENTS-SECTION.md` catalog under the right class (always-on cron or heartbeat-toggled burst). Keep the one-line description tight.
- Add an entry to `templates/crons.md` with schedule and enable logic.
- If it is a burst worker, reference it from `HEARTBEAT-SECTION.md` where the orchestrator decides to enable or disable it.
- Update `INSTALL_FOR_AGENTS.md`'s smoke-test cron-name list.
- Add a changelog entry in `CHANGELOG.md` for the next version draft.

The install command lives inside the routine spec, not in a separate file. Operators reading the spec see exactly what would register.

## Copy-paste template

```markdown
# <routine-name>

<One-sentence description with class>. Always-on cron | Heartbeat-toggled burst.

## References

- <convention doc>
- <companion routine>

## Authority

<what it can do, what it cannot>.

## Trigger

<cron schedule + enable logic>.

## Approval gates

- <obvious -> just act>
- <ambiguous -> surface in the reply>

## Escalation

<unusual states that halt the routine and appear in the reply>.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

## What to do

1. <step one>.
2. <step two>.
3. <step three>.

## What NOT to do

- Never <X>.
- Do not <Y>.

## Reply

Single line. `NO_REPLY` for quiet runs:

\`\`\`
<routine-name>: <fields>
\`\`\`

Or:

\`\`\`
NO_REPLY
\`\`\`

## Install

Prerequisite: `clawstodian/routines` symlink to `~/clawstodian/routines`.

\`\`\`bash
openclaw cron add \
  --name <routine-name> \
  --every 30m \
  [--disabled] \
  --session isolated \
  --light-context \
  --announce --channel discord --to "channel:<your-logs-channel-id>" \
  --message "Read clawstodian/routines/<routine-name>.md and execute."
\`\`\`

## Verify

\`\`\`bash
openclaw cron list --all | grep <routine-name>
\`\`\`

## Uninstall

\`\`\`bash
openclaw cron remove <routine-name>
\`\`\`
```
