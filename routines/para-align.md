# para-align (routine)

Verifies PARA structural and semantic health across the full graph, applies trivial fixes, and surfaces the rest.

## Program

`clawstodian/programs/para.md` - conventions, authority, approval gates, and escalation.

## Target

The full PARA graph: all entities in `projects/`, `areas/`, `resources/`, `archives/`, plus `MEMORY.md` at workspace root.

## Scope

Four dimensions:

1. **Structural integrity** - frontmatter schema, `INDEX.md` coverage, `related:` pointer resolution.
2. **Cross-reference consistency** - when an entity moves or is renamed, every referrer updates; when an entity is deleted or archived, nothing still points at its old path.
3. **Naming and slug conventions** - kebab-case, no spaces, no underscores, lowercase; consistent with `memory/para-structure.md`.
4. **MEMORY.md currency** - every active project listed; retired projects not listed under active; infrastructure and area pointers resolve.

## Steps

1. **Walk the graph.** For each entity file in `projects/`, `areas/`, `resources/`, `archives/`:
   - Frontmatter matches `memory/para-structure.md`.
   - `related:` pointers resolve to existing files.
   - The entity is listed in the relevant `INDEX.md`.
   - The filename follows naming conventions.
2. **Check cross-references.**
   - For every `related:` pointer, verify the target exists at the given path.
   - For every entity path mentioned in `MEMORY.md` or in another entity's body, verify it resolves.
   - If a target moved or was renamed and the new path is unambiguous (slug differs only by known convention change), update the referrer.
   - If a target appears deleted or archived and no replacement is obvious, surface.
3. **Verify `MEMORY.md`.** Every project with `status: active` appears individually; retired or archived projects do not; infrastructure pointers resolve; top-level structure sections match reality. Rebuild the dashboard in place if drifted; the dashboard is a summary of current state, not a historical record.
4. **Classify findings.**
   - **Trivial structural fix** (missing `INDEX.md` entry, frontmatter whitespace, inferrable `last_updated`, broken `related:` pointer with obvious replacement, MEMORY.md dashboard sections out of date): apply in place.
   - **Anything else** (entity content, path, status semantics, ambiguous `related:` target, slug rename with downstream implications, new top-level folder): do NOT rewrite. Surface with file path, observed state, proposed fix.

## Commit

Add only the files you changed. Commit message: `para: align YYYY-Www - <summary>`. Push immediately. If no trivial fixes were applied, there is nothing to commit.

## Exec safety

- Run commands by exact path. No `eval`, `bash -c "..."`, or other indirection that hides the real command from the gateway's exec safety layer.
- For multi-line script logic, write the script to `/tmp/clawstodian-para-align-<context>.py` (or `.sh`) and invoke it by path. Do not inline code via heredoc to an interpreter (`python3 <<EOF ... EOF`); the safety layer blocks that as obfuscation.
- `jq` and `python3 -c '<short expression>'` one-liners are fine when they fit on one line and the intent is obvious.

## Worker discipline

- Single-run job. Walk the graph, classify findings, apply trivial fixes, surface the rest.
- Apply only the trivial structural fixes the program authorizes. Everything else surfaces in the run report.
- No self-disable; this cron is scheduled, not queue-driven. The heartbeat orchestrator may `--wake now` this routine mid-week if `para-extract` reports drift it cannot safely resolve.

## Run report

Two artifacts per firing: a full report on disk following the shared run-report shape, and a multi-line scannable summary posted to the notifications channel.

### File on disk

Write to `memory/runs/para-align/<YYYY-MM-DD>T<HH-MM-SS>Z.md`.

```markdown
# para-align run report

- timestamp: 2026-04-20T06:00:00Z
- context: 2026-W16
- outcome: fixes-applied

## What happened

### Verified

- entities scanned: 48
- frontmatter-ok: 47
- frontmatter-violations: 1 (see Surfaced for operator)
- cross-references-ok: 48
- broken cross-references: 0
- MEMORY.md current: yes

### Trivial fixes applied

- 3
  - projects/vps-migration/README.md - normalized `status` value `Active` → `active`
  - resources/1password-secrets-management.md - added missing `last_updated`
  - areas/people/alice.md - removed stale `related` entry

## Commits

- 7aa12bc para: align 2026-W16 - 3 trivial fixes

## Surfaced for operator

- 1 proposal
  - projects/unnamed-project/README.md - `type: project` but no `status` field and unclear ownership. Suggested action: ask operator whether to archive or promote.

## Channel summary

para-align · 2026-W16 · fixes-applied
Verified: 48 entities (clean=47, violations=1)
Trivial fixes: 3 applied
Proposals: 1 awaiting operator
Report: memory/runs/para-align/2026-04-20T06-00-00Z.md
```

### Channel summary

Multi-line. One insight per line:

```
para-align · <ISO-week> · <outcome>
Verified: <N> entities (clean=<C>, violations=<V>)
Trivial fixes: <M> applied
Proposals: <K> awaiting operator
Report: memory/runs/para-align/<ts>.md
```

- `outcome` is `clean | fixes-applied | proposals-surfaced | failed` (use the most-significant one if several apply).
- Omit the "Trivial fixes" line when `M` is 0 on a clean graph.
- Omit the "Proposals" line when `K` is 0.

Even a clean graph produces both artifacts (no `NO_REPLY`); the weekly health signal is valuable.
