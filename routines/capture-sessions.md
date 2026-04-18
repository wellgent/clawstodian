# capture-sessions (routine)

Admits new sessions into the ledger and drains interactive capture gaps into the appropriate daily note(s) per the daily-notes program.

## Program

`clawstodian/programs/daily-notes.md` - follow the "Capture one session's new content" behavior (including gap enumeration, target selection, classification, turn filtering, date bucketing, and cursor-advance discipline). The program describes one session's unit of work; this routine decides how many units to process per firing.

## Target

All capture gaps in `sessions_list` vs. `memory/session-ledger.md`:

- **un-admitted**: present in `sessions_list` but absent from the ledger.
- **stale**: ledger entry exists, but `sessions_list` row's `updatedAt > ledger.last_activity`.

Within each kind, prioritize by newest `updatedAt` so live sessions capture before historical drain.

## Exec safety

- Run commands by exact path. No `eval`, `bash -c "..."`, or other indirection that hides the real command from the gateway's exec safety layer.
- For multi-line script logic, write the script to `/tmp/clawstodian-capture-<context>.py` (or `.sh`) and invoke it by path. Do not inline code via heredoc to an interpreter (`python3 <<EOF ... EOF`); the safety layer blocks that as obfuscation.
- `jq` and `python3 -c '<short expression>'` one-liners are fine when they fit on one line and the intent is obvious.

## Worker discipline

Two phases per firing.

**Phase 1 - admit all un-admitted sessions.** Classification is cheap (check `kind`, look for user messages). For every session in `sessions_list` with no ledger entry, classify and append an entry. No per-firing cap on Phase 1: if there are 40 un-admitted cron sessions, admit all 40. A single append of multiple H2 blocks at the end of the ledger is fine; narrow per-line edits are unnecessary for brand-new entries. Skipped admissions produce ledger entries with `classification: skipped` and a short `reason`; interactive admissions produce `classification: interactive` with `lines_captured: 0` and await Phase 2 for their first read.

**Phase 2 - process interactive gaps, bounded.** Enumerate interactive gaps (both the `lines_captured: 0` admissions from Phase 1 AND pre-existing stale-cursor entries). Sort by `updatedAt` descending. Process one at a time per the program's reading-layer rules. After each session, continue to the next-newest gap until ANY of these hold:

- No interactive gaps remain.
- The firing is approaching its budget (rough target: stop once ~80 KB of JSONL has been read across all sessions processed, or when the agent's own context is past ~80 K tokens). Leave headroom for the self-disable check and run report.
- Five interactive sessions have been processed this firing (hard cap to prevent runaway on pathological queues).

If Phase 2 runs out of budget with interactive gaps still remaining, the cron stays enabled and the next firing picks up from the newest remaining gap.

**Discipline across phases:**

- Read JSONL with `Read` from `lines_captured + 1`, or from offset 0 for a newly-admitted interactive session. Do not re-read from 0 when the ledger has a cursor.
- Write daily-note updates FIRST, then advance the ledger cursor for that session. If either step fails, leave the cursor at its old position so the next firing retries.
- Never mutate a sealed daily note. Content for a sealed date goes into the `bleed_over` accumulator for the run report.
- Cursor edits to `memory/session-ledger.md` are narrow `Edit` calls on the matching lines, not full rewrites.

## Self-disable on empty queue

After Phase 2 returns, re-count un-admitted and stale-cursor sessions. If both are zero, disable the cron:

```bash
openclaw cron disable capture-sessions
```

**Cron safety: disable means `openclaw cron disable`, NEVER `openclaw cron remove`.** Remove deletes the cron permanently.

## Run report

Single line delivered to the logs channel by the cron runner:

```
capture-sessions: admitted <N> (skipped=<s>, interactive=<i>) | captured <M> sessions | dates [YYYY-MM-DD, ...] | merged <X> slugs | filed <Y> insights | bleed <Z> sealed | queue: un-admitted=<u>/stale=<s2> | cron: <enabled|disabled>
```

- `admitted` - total ledger entries added this firing; `skipped` and `interactive` sum to it.
- `captured` - interactive sessions whose cursor advanced (includes Phase 1 admissions that got a Phase 2 first-read).
- `dates` - union of all `dates_touched` values updated this firing.
- `queue` - counts remaining after the firing; drives the heartbeat's next toggle decision.

Return `NO_REPLY` when `admitted` is 0 OR all admissions were `skipped`, AND `captured` is 0, AND the cron state did not change. All three conditions together mean the firing produced no observable effect.

Always report when: any interactive capture happened (`captured > 0`), any bleed surfaced (`bleed > 0`), or the cron self-disabled (state transition).
