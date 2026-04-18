# para-extract (routine)

Every 30 minutes while enabled. Drains the PARA extraction queue one sealed note per run per the para program.

Starts disabled. The heartbeat orchestrator enables the cron when sealed notes with `para_status: pending` exist and disables it when the queue is empty.

## Program

`clawstodian/programs/para.md` - follow the "Extract PARA from a sealed note" behavior (including queue definition, target selection, and steps).

## Target

The oldest queued sealed note: `memory/YYYY-MM-DD.md` with frontmatter `status: sealed` and `para_status: pending`.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

## Worker discipline

- Process exactly one note per firing. Do not drain the queue in a single run.
- Touch only the frontmatter fields the program allows (`para_status`, `last_updated`).
- If the program's approval gates say "surface" on a candidate entity, do not create; surface it in the run report.

## Self-disable on empty queue

After processing, re-check the queue. If empty, disable the cron:

```bash
openclaw cron disable para-extract
```

**Cron safety: disable means `openclaw cron disable`, NEVER `openclaw cron remove`.** Remove deletes the cron permanently.

## Run report

Single line delivered to the logs channel by the cron runner:

```
para-extract YYYY-MM-DD: <processed|skipped|failed> | entities <N updated, M created, K ambiguous> | queue: <remaining> | cron: <enabled|disabled>
```

Never return `NO_REPLY` on a processed note; each run carries state transition worth seeing.
