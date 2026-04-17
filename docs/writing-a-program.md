# Writing a clawstodian program

Programs are the unit of work in clawstodian. A program is a markdown spec under `programs/` that defines a named, scoped, repeatable chunk of workspace maintenance. This guide is for anyone extending the package - adding a new heartbeat-direct program, a new burst worker, a new fixed cron, or something between them.

## Pick the pattern first

| Class | Trigger | Schedule | Use when |
| --- | --- | --- | --- |
| **Heartbeat-direct** | `HEARTBEAT.md` coordinator each tick | Heartbeat cadence | Continuous maintenance that should run every tick |
| **Heartbeat-inline** | Called from within another program | Inherited | A subroutine that fits as a child, not a peer |
| **Burst worker** | Cron, heartbeat toggles enabled state | `--every 30m` (while enabled) | A queue that accumulates and needs to be drained |
| **Fixed cron** | Cron on its own schedule | `--cron "<expr>"` | A real wall-clock requirement (e.g. Sunday 06:00) |

Preference order when more than one fits: heartbeat-direct > heartbeat-inline > burst worker > fixed cron. The further down, the more moving parts.

## Anatomy

Every program uses the same anatomy, adapted from OpenClaw's [standing-orders](https://docs.openclaw.ai/automation/standing-orders) pattern. Section order matters - operators read top-to-bottom to understand the program.

```markdown
# <program-name>

One-sentence description with the program class (e.g. "Heartbeat-direct: keep today's canonical note current.").

## References

- Convention docs this program relies on (e.g. `memory/daily-note-structure.md`).
- Companion programs (e.g. "Burst worker for past days -> `clawstodian/programs/close-of-day.md`").

## Authority

What the program is permitted to do. Tools it uses. Files it creates, reads, or edits. What it must not touch.

## Trigger

What invokes this program. For heartbeat programs: the task and cadence. For crons: the schedule and enable/disable logic.

## Approval gates

Which actions need operator confirmation, which do not. One or two short bullets.

## Escalation

Which unusual states should be surfaced and halt the program. Name them explicitly.

## Exec safety (cron routines)

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

## What to do

Numbered steps. Explicit, specific, ordered.

## What NOT to do

Bullet list of prohibitions. "Never X" / "Do not Y".

## Install (cron routines only)

<install block - see conventions below>

## Verify (cron routines only)

<verification commands>
```

Heartbeat-only programs omit Exec safety / Install / Verify.

## Install command conventions

Every cron routine's install command follows the same shape:

```bash
openclaw cron add \
  --name <program-name> \              # matches spec filename without .md
  --every 30m | --cron "<expr>" \      # schedule (pick one)
  [--disabled] \                       # burst workers only
  --session isolated \                 # always isolated for maintenance
  --light-context \                    # always; the spec loads what it needs
  --announce --channel <channel> --to "channel:<your-logs-channel-id>" \
  --message "Read clawstodian/programs/<program-name>.md and execute."
```

Flag notes:

- **`--name`** matches the spec filename minus `.md`. That name is how `memory/crons.md`, the heartbeat coordinator, and operators refer to the job.
- **`--every`** for demand-driven bursts (30m is the clawstodian default). **`--cron`** for wall-clock-bound schedules. Never both.
- **`--disabled`** on burst workers only. Heartbeat will enable on demand. Omit for fixed crons.
- **`--session isolated`** always for maintenance crons. Do not use `--session current` - it captures an ephemeral TUI or DM session key that drifts and orphans cron-session entries over time.
- **`--light-context`** always. Bootstrap files are not needed; the program reads its own spec and the references it lists.
- **`--announce --channel --to`** routes summaries to the operator's maintainer logs channel. Substitute `--no-deliver` if the operator explicitly wants silent runs.
- **`--message`** is always `"Read clawstodian/programs/<name>.md and execute."` The spec is the authority; the cron payload is just the dispatch.

## Sessions: what to pass and what to leave alone

For maintenance crons, **do not set a sessionKey**. `--session isolated` alone produces a session-store entry named `agent:<agentId>:cron:<jobId>` automatically. Isolated per job, stable across runs, no conversation context inherited.

Rule of thumb: if you did not deliberately choose to tie a cron to a specific conversation, the sessionKey should be empty.

## Delivery: announce by default, auto-silent on empty

The runner owns the final delivery path for isolated crons. Whatever plain-text summary the agent returns becomes the announcement. If the agent returns `NO_REPLY` or an empty reply, delivery is suppressed automatically.

A noisy-announce cron with a quiet program produces silent runs without explicit configuration. Prefer `--announce` over `--no-deliver` as the default and let reply shape determine noise.

## Catalog integration

When you ship a new program:

- Add the program to `AGENTS-SECTION.md` catalog under the right class. Keep the one-line description tight.
- If it is a cron routine, add an entry to `templates/crons.md`.
- If it is heartbeat-direct or heartbeat-inline, reference it from `HEARTBEAT-SECTION.md` where the coordinator decides to run it.
- Add a changelog entry in `CHANGELOG.md` for the next version draft.

The install command lives inside the program spec, not in a separate file. Operators reading the spec see exactly what would register.

## Copy-paste template

Strip the sections that do not apply to your class (heartbeat programs do not need Exec safety / Install / Verify).

```markdown
# <program-name>

<One-sentence description with class>.

## References

- <convention doc>
- <companion program>

## Authority

<what it can do, what it cannot>.

## Trigger

<heartbeat task + cadence, or cron schedule + enable logic>.

## Approval gates

- <obvious -> just act>
- <ambiguous -> ask the operator>

## Escalation

<unusual states that halt the program>.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

## What to do

1. <step one>.
2. <step two>.
3. <step three>.

## What NOT to do

- Never <X>.
- Do not <Y>.

## Install

Prerequisite: the workspace has a `clawstodian/programs` symlink to `~/clawstodian/programs`.

\`\`\`bash
openclaw cron add \
  --name <program-name> \
  --every 30m \
  --disabled \
  --session isolated \
  --light-context \
  --announce --channel discord --to "channel:<your-logs-channel-id>" \
  --message "Read clawstodian/programs/<program-name>.md and execute."
\`\`\`

## Verify

\`\`\`bash
openclaw cron list --all | grep <program-name>
\`\`\`
```
