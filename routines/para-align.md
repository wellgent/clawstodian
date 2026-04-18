# para-align (routine)

Verifies PARA structural and semantic health across the full graph per the para program.

## Program

`clawstodian/programs/para.md` - follow the "Align PARA structure" behavior.

## Target

The full PARA graph: all entities in `projects/`, `areas/`, `resources/`, `archives/`, plus `MEMORY.md` at workspace root.

## Exec safety

- Run commands by exact path. No `eval`, `bash -c "..."`, or other indirection that hides the real command from the gateway's exec safety layer.
- For multi-line script logic, write the script to `/tmp/clawstodian-para-align-<context>.py` (or `.sh`) and invoke it by path. Do not inline code via heredoc to an interpreter (`python3 <<EOF ... EOF`); the safety layer blocks that as obfuscation.
- `jq` and `python3 -c '<short expression>'` one-liners are fine when they fit on one line and the intent is obvious.

## Worker discipline

- Single-run job. Walk the graph, classify findings, apply trivial fixes, surface the rest.
- Apply only the trivial structural fixes the program authorizes. Everything else surfaces in the run report.
- No self-disable; this cron is scheduled, not queue-driven. The heartbeat orchestrator may `--wake now` this routine mid-week if `para-extract` reports drift it cannot safely resolve.

## Run report

Two artifacts per firing: a full report on disk and a one-line summary to the notifications channel.

### File on disk

Write to `memory/runs/para-align/<YYYY-MM-DD>T<HH-MM-SS>Z.md`.

File shape:

```markdown
# para-align run report

- timestamp: 2026-04-20T06:00:00Z
- week: 2026-W16
- outcome: clean | fixes-applied | proposals-surfaced | failed

## Verified

- entities scanned: 48
- frontmatter-ok: 47
- frontmatter-violations: 1 (see proposals)
- cross-references-ok: 48
- broken cross-references: 0
- MEMORY.md current: yes

## Trivial fixes applied

- 3
  - projects/vps-migration/README.md - normalized `status` value `Active` -> `active`
  - resources/1password-secrets-management.md - added missing `last_updated`
  - areas/people/alice.md - removed stale `related` entry

## Proposals (awaiting operator)

- 1
  - projects/unnamed-project/README.md - `type: project` but no `status` field and unclear ownership. Suggested action: ask operator whether to archive or promote.

## Channel summary

para-align 2026-W16: verified 48 entities | trivial fixes 3 | proposals 1 (awaiting operator) | report: memory/runs/para-align/2026-04-20T06-00-00Z.md
```

### Channel summary

```
para-align YYYY-Www: verified <N> entities | trivial fixes <M> | proposals <K> (awaiting operator) | report: memory/runs/para-align/<ts>.md
```

Even a clean graph produces both artifacts (no `NO_REPLY`); the weekly health signal is valuable.
