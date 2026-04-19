# para-align (routine)

Verifies PARA structural and semantic health across the full graph, applies trivial fixes, and surfaces the rest.

## Program

`clawstodian/programs/para.md` - conventions, authority, approval gates, and escalation.

## Target

The full PARA graph: all entities in `projects/`, `areas/`, `resources/`, `archives/`, plus `MEMORY.md` at workspace root.

## Scope

Six dimensions:

1. **Structural integrity** - frontmatter schema, `INDEX.md` coverage, `related:` pointer resolution.
2. **Cross-reference consistency** - when an entity moves or is renamed, every referrer updates; when an entity is deleted or archived, nothing still points at its old path.
3. **Naming and slug conventions** - kebab-case, no spaces, no underscores, lowercase; consistent with `memory/para-structure.md`.
4. **MEMORY.md currency** - every active project listed; retired projects not listed under active; infrastructure and area pointers resolve.
5. **Semantic freshness** - active projects and key areas (people, companies, servers) reflect recent workspace activity. An entity with meaningful mentions in sealed daily notes from the last 7 days after its `last_updated` is semantically stale. Resources are excluded; reference material is meant to be stable and staleness there means something different.
6. **Archive candidacy** - projects and resources showing sustained inactivity are candidates for archival. Signals: stale `last_updated` (60+ days), no daily-note mentions in the recent window (30+ days), body-level indicators of completion or abandonment (milestones all marked done, "shipped" / "closed" / "superseded" language). Surface only; never move. Actual archival is always an operator decision.

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
4. **Semantic freshness check.** For each active project in `projects/` and each entity in `areas/people/`, `areas/companies/`, `areas/servers/`:
   - Read the entity's `last_updated`.
   - Grep for its slug (and obvious title variants) across sealed daily notes from the last 7 days.
   - For each matching note dated newer than the entity's `last_updated`: if the mention carries meaningful content (decision, status change, outcome, substantive context - not a passing reference), record as drift. Ignore incidental mentions.
   - Surface each drift case with: entity path, entity `last_updated`, list of mentioning notes with dates, one-line characterization of what the notes add that the entity does not reflect.
   - Do NOT write entity content. Surfacing is the entire action; resolution is an operator decision (update the entity in-session, or re-enqueue affected notes for `para-extract` by resetting their `para_status` to `pending`).
5. **Archive candidacy check.** For each project in `projects/` with `status: active` and each resource in `resources/`:
   - Compare `last_updated` against a 60-day threshold. If fresher, skip.
   - Grep for the entity's slug across sealed daily notes from the last 30 days. If any meaningful mentions, skip (that is semantic-freshness territory, not archive territory).
   - Read the entity body for completion / abandonment signals: milestones all marked done, explicit "shipped" / "closed" / "superseded by X" language, no open next-steps. This is a soft boost, not required.
   - Record as archive candidate with: entity path, `last_updated`, days since last mention in daily notes, body-level evidence (or "none") supporting the candidacy, one-line recommendation ("consider archive", "superseded by <path>", etc.).
   - Reuse the daily-note read from step 4 where possible; these checks share inputs (`last_updated`, recent sealed notes).
   - Do NOT move entities into `archives/`. Do NOT change entity `status`. Surfacing is the entire action.
6. **Classify findings.**
   - **Trivial structural fix** (missing `INDEX.md` entry, frontmatter whitespace, inferrable `last_updated`, broken `related:` pointer with obvious replacement, MEMORY.md dashboard sections out of date): apply in place.
   - **Semantic drift** (entity stale relative to recent workspace activity): always surface, never auto-fix. PARA-entity content authorship is not this routine's job.
   - **Archive candidate** (entity shows sustained inactivity): always surface, never auto-move. Archival is an operator decision.
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
- Semantic-freshness detection is read-only: grep and compare, never mutate entity content based on daily-note inference. That is `para-extract`'s (and in-session agents') territory.
- Archive candidacy detection is read-only: compare timestamps and body signals, never move files between buckets, never change `status`. Archival is an operator decision.
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

### Semantic freshness

- entities checked: 17 (projects=8, areas/people=6, areas/companies=2, areas/servers=1)
- drift flagged: 2
  - projects/vps-migration/README.md - last_updated 2026-04-05; memory/2026-04-12.md and memory/2026-04-15.md record migration progress (Stripe cutover, DNS rollover) not reflected in entity body
  - areas/people/alice.md - last_updated 2026-03-20; memory/2026-04-14.md records a pricing decision that updates her relationship context

### Archive candidacy

- entities checked: 11 (projects with status: active=8, resources=3)
- candidates flagged: 2
  - projects/legacy-reporting/README.md - last_updated 2025-11-04; no daily-note mentions in last 30 days; body notes "shipped 2025-11" and all next-steps marked done. Recommendation: consider archive.
  - resources/gitlab-to-github-migration-runbook.md - last_updated 2025-10-12; no recent mentions; "superseded by resources/github-actions-migration.md" in body. Recommendation: archive (pointer to successor exists).

## Commits

- 7aa12bc para: align 2026-W16 - 3 trivial fixes

## Surfaced for operator

- 1 structural proposal
  - projects/unnamed-project/README.md - `type: project` but no `status` field and unclear ownership. Suggested action: ask operator whether to archive or promote.
- 2 semantic drift flags (see "Semantic freshness" above)
- 2 archive candidates (see "Archive candidacy" above)

## Channel summary

para-align · 2026-W16 · fixes-applied
Verified: 48 entities (clean=47, violations=1)
Trivial fixes: 3 applied
Drift: 2 entities flagged
Archive: 2 candidates
Proposals: 1 awaiting operator
Report: memory/runs/para-align/2026-04-20T06-00-00Z.md
```

### Channel summary

Multi-line. One insight per line:

```
para-align · <ISO-week> · <outcome>
Verified: <N> entities (clean=<C>, violations=<V>)
Trivial fixes: <M> applied
Drift: <D> entities flagged
Archive: <A> candidates
Proposals: <K> awaiting operator
Report: memory/runs/para-align/<ts>.md
```

- `outcome` is `clean | fixes-applied | proposals-surfaced | failed` (use the most-significant one if several apply). Semantic drift and archive candidates roll into `proposals-surfaced` when they are the only findings, since drift flags and archive candidates are both proposals for the operator.
- Omit the "Trivial fixes" line when `M` is 0 on a clean graph.
- Omit the "Drift" line when `D` is 0.
- Omit the "Archive" line when `A` is 0.
- Omit the "Proposals" line when `K` is 0.

Even a clean graph produces both artifacts (no `NO_REPLY`); the weekly health signal is valuable.
