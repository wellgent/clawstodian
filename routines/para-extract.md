# para-extract (routine)

Processes one sealed note per firing per the para program.

## Program

`clawstodian/programs/para.md` - follow the "Extract PARA from a sealed note" behavior (including queue definition, target selection, and steps).

## Target

The oldest queued sealed note: `memory/YYYY-MM-DD.md` with frontmatter `status: sealed` and `para_status: pending`.

## Exec safety

- Run commands by exact path. No `eval`, `bash -c "..."`, or other indirection that hides the real command from the gateway's exec safety layer.
- For multi-line script logic, write the script to `/tmp/clawstodian-para-extract-<context>.py` (or `.sh`) and invoke it by path. Do not inline code via heredoc to an interpreter (`python3 <<EOF ... EOF`); the safety layer blocks that as obfuscation.
- `jq` and `python3 -c '<short expression>'` one-liners are fine when they fit on one line and the intent is obvious.

## Worker discipline

- One note per firing. Do not drain the queue in a single run.
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
