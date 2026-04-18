# para-align (routine)

Sunday 06:00 UTC, always enabled. Verifies PARA structural and semantic health across the full graph per the para program. The heartbeat orchestrator may also `--wake now` this routine mid-week if `para-extract` reports drift it cannot safely resolve.

## Program

`clawstodian/programs/para.md` - follow the "Align PARA structure" behavior.

## Target

The full PARA graph: all entities in `projects/`, `areas/`, `resources/`, `archives/`, plus `MEMORY.md` at workspace root.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

## Worker discipline

- Single-run job. Walk the graph, classify findings, apply trivial fixes, surface the rest. No self-disable; the cron is scheduled weekly regardless.
- Apply only the trivial structural fixes the program authorizes. Everything else surfaces in the run report.

## Run report

Single line delivered to the logs channel by the cron runner:

```
para-align YYYY-Www: verified <N> entities | trivial fixes <M> | proposals <K> (awaiting operator)
```

Even a clean graph produces a report (no `NO_REPLY`); the weekly health signal is valuable.
