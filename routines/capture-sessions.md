# capture-sessions (routine)

Processes one session's unread JSONL into the appropriate daily note(s) per the daily-notes program.

## Program

`clawstodian/programs/daily-notes.md` - follow the "Capture one session's new content" behavior (including gap enumeration, target selection, classification, turn filtering, date bucketing, and cursor-advance discipline).

## Target

The single session with the newest `updatedAt` among those with a gap:

- **un-admitted**: present in `sessions_list` but absent from `memory/session-ledger.md`.
- **stale**: present in ledger, but `sessions_list` row's `updatedAt > ledger.last_activity`.

Selecting by newest `updatedAt` prioritizes live sessions over historical drain.

## Exec safety

- Run commands by exact path. No `eval`, `bash -c "..."`, or other indirection that hides the real command from the gateway's exec safety layer.
- For multi-line script logic, write the script to `/tmp/clawstodian-capture-<context>.py` (or `.sh`) and invoke it by path. Do not inline code via heredoc to an interpreter (`python3 <<EOF ... EOF`); the safety layer blocks that as obfuscation.
- `jq` and `python3 -c '<short expression>'` one-liners are fine when they fit on one line and the intent is obvious.

## Worker discipline

- One session per firing. Do not loop to the next gap even if capacity remains.
- Read JSONL with `Read` from `lines_captured + 1`, or from offset 0 for a newly-admitted interactive session. Do not re-read from 0 when the ledger has a cursor.
- Write daily-note updates FIRST, then advance the ledger cursor. If either step fails, leave the cursor at its old position so the next firing retries.
- Never mutate a sealed daily note. Content for a sealed date goes into the `bleed_over` accumulator.
- Cursor edits to `memory/session-ledger.md` are narrow `Edit` calls on the matching lines, not full rewrites.

## Self-disable on empty queue

After processing, re-check both gap conditions: un-admitted count AND stale-cursor count. If both are zero, disable the cron:

```bash
openclaw cron disable capture-sessions
```

**Cron safety: disable means `openclaw cron disable`, NEVER `openclaw cron remove`.** Remove deletes the cron permanently.

## Run report

Single line delivered to the logs channel by the cron runner:

```
capture-sessions <sid-prefix>: <captured|admitted-skipped|failed> | classification: <interactive|skipped:<reason>> | lines: <from>-><to> | dates: [YYYY-MM-DD, ...] | merged <M> slugs | filed <K> insights | bleed <B> sealed | queue: un-admitted=<u>/stale=<s> | cron: <enabled|disabled>
```

Return `NO_REPLY` when the firing's only outcome was admitting a `skipped`-classified session (cron, hook, subagent, delivery-only).

Always report: interactive captures, failures, queue-becomes-empty self-disable firings.
