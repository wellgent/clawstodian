# para-align

Verify PARA structural and semantic health. Apply trivial structural fixes; surface everything else.

## References

- PARA conventions -> `memory/para-structure.md`
- Daily note format -> `memory/daily-note-structure.md`
- Workspace dashboard -> `MEMORY.md` at workspace root

Read `memory/para-structure.md` before starting. It defines the conventions you are validating against.

## Authority

- Read every entity in `projects/`, `areas/`, `resources/`, `archives/`.
- Apply trivial structural fixes in place: missing `INDEX.md` entry, frontmatter whitespace, obviously-inferable `last_updated`.
- Update `MEMORY.md` dashboard to reflect current active projects, area pointers, and infrastructure references.
- Update `related:` pointers after confirmed entity renames or moves (operator-confirmed or obvious from file-presence evidence only).
- Propose all non-trivial fixes in the summary; do not apply them.

## Scope

Covers four dimensions of PARA health:

1. **Structural integrity** - frontmatter schema, `INDEX.md` coverage, `related:` pointer resolution.
2. **Cross-reference consistency** - when an entity file moves or is renamed, every referrer updates; when a file is deleted or archived, nothing still points at its old path.
3. **Naming and slug conventions** - kebab-case, no spaces, no underscores, lowercase; consistent with `memory/para-structure.md`.
4. **MEMORY.md currency** - every active project is listed; retired projects are not; infrastructure and area pointers resolve.

## Approval gates

- Trivial structural fixes: apply in place.
- Entity content, path, status semantics, ambiguous `related:` target, slug rename with downstream implications, new top-level folder: surface; do not apply.

## Escalation

- A rename that would update many referrers ambiguously: surface the set of proposed changes; wait.
- A structural anomaly that looks intentional (e.g. an entity is non-conforming because a plugin created it): surface; do not correct.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

## What to do

**1. Walk the graph.**

For each entity file in `projects/`, `areas/`, `resources/`, `archives/`:
- Frontmatter matches `memory/para-structure.md` (required common fields, type-specific fields, valid status values).
- `related:` pointers resolve to existing files.
- The entity is listed in the relevant `INDEX.md`.
- The filename follows naming conventions (kebab-case, no spaces, lowercase).

**2. Check cross-references.**

- For every `related:` pointer, verify the target file exists at the given path.
- For every entity path mentioned in `MEMORY.md` or in another entity's body, verify it resolves.
- If a target moved or was renamed and the new path is unambiguous (e.g. old and new both in index history; slug differs only by known convention change), update the referrer.
- If a target appears deleted or archived and no replacement is obvious, surface in the summary.

**3. Verify `MEMORY.md`.**

- Every project with `status: active` appears individually in the dashboard.
- Retired or archived projects are not listed under active.
- Infrastructure pointers (servers, tools, external systems) resolve.
- The "Knowledge Graph" / "PARA folders" / "Quick navigation" sections reflect current top-level structure.

If MEMORY.md has drifted, update it in place. The dashboard is the summary of current state; rebuilding it is trivial structural work.

**4. Classify findings.**

For each discrepancy from steps 1-3:
- **Trivial structural fix** (missing `INDEX.md` entry, frontmatter whitespace, inferrable `last_updated`, broken `related:` pointer with obvious replacement, MEMORY.md dashboard sections out of date): apply in place.
- **Anything else** (entity content, path, status semantics, ambiguous `related:` target, slug rename with downstream implications, new top-level folder): do NOT rewrite. Surface in the summary with file path, observed state, proposed fix. The operator decides.

## Commit

Add only the files you changed - never `git add -A`. Commit message: `para: align YYYY-Www - <summary>`. Push immediately after the commit. No AI attribution lines.

## What NOT to do

- Do not rewrite entity content for style or brevity.
- Do not move, rename, or delete files based on your own judgment; moves are operator decisions.
- Do not modify `AGENTS.md`, `HEARTBEAT.md`, or anything in `.openclaw/`.
- Do not disable or enable any cron.
- Do not auto-archive inactive projects (archive lifecycle is user-managed).

## Summary

Report one line:

```
para-align YYYY-Www: verified <N> entities | trivial fixes <M> | proposals <K> (awaiting operator)
```
