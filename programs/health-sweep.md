# health-sweep

Surface anomalies across the workspace with likely causes. Collaborate on resolution; do not auto-repair. Heartbeat-direct: same tick as `workspace-tidiness` and `git-hygiene`.

## References

- Related programs (same tick) -> `clawstodian/programs/workspace-tidiness.md`, `clawstodian/programs/git-hygiene.md`
- Cron map -> `memory/crons.md`
- Clawstodian reference docs -> `memory/para-structure.md`, `memory/daily-note-structure.md`, `MEMORY.md`

## Authority

Read-only by default.

- Read configs, cron logs, template files, symlink targets, heartbeat state.
- Report findings; propose resolution paths.

Any fix requires explicit operator confirmation.

## Trigger

Heartbeat task `workspace-sweep` on interval, folded with `workspace-tidiness` and `git-hygiene`.

## Approval gates

Read-only by default. Any change action requires the operator's explicit go-ahead.

## Escalation

Everything this program finds is already an escalation by design: surface what you see.

## What to do

1. Check recent cron run logs for failures; report the last 1-2 failure reasons per failed job.
2. Compare installed clawstodian reference docs (`memory/para-structure.md`, `memory/daily-note-structure.md`, `MEMORY.md`, `memory/crons.md`) against the clawstodian-authoritative copies; report meaningful drift.
3. Check heartbeat config matches the recommended stance: `isolatedSession: true`, `target` set to a real channel, `activeHours` set, channel visibility `showOk: false` and `showAlerts: true`.
4. Check workspace symlinks resolve.
5. Report findings with, for each: what was observed, the likely cause, and one or two resolution paths.

## What NOT to do

- Do not rewrite configs unless the operator explicitly asked for it.
- Do not overwrite workspace docs blindly.
- Do not restart services just to clear a warning.
- Do not disable heartbeat.
- Do not touch anything in `.openclaw/` without confirmation.
