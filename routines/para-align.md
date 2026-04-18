# para-align

Verify PARA structural and semantic health. Apply trivial structural fixes; surface everything else. Fixed cron: weekly by default; heartbeat may trigger mid-week if `para-extract` reports drift.

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
- Propose all non-trivial fixes in the reply; do not apply them.

## Scope

Covers four dimensions of PARA health:

1. **Structural integrity** - frontmatter schema, `INDEX.md` coverage, `related:` pointer resolution.
2. **Cross-reference consistency** - when an entity file moves or is renamed, every referrer updates; when a file is deleted or archived, nothing still points at its old path.
3. **Naming and slug conventions** - kebab-case, no spaces, no underscores, lowercase; consistent with `memory/para-structure.md`.
4. **MEMORY.md currency** - every active project is listed; retired projects are not; infrastructure and area pointers resolve.

## Trigger

Cron-scheduled weekly (Sunday 06:00 UTC by default; see Install). The heartbeat orchestrator may also `--wake now` this routine mid-week when `para-extract` reports drift it cannot safely resolve.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters; the gateway's exec safety layer blocks that as obfuscation.

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
- If a target appears deleted or archived and no replacement is obvious, surface in the reply.

**3. Verify `MEMORY.md`.**

- Every project with `status: active` appears individually in the dashboard.
- Retired or archived projects are not listed under active.
- Infrastructure pointers (servers, tools, external systems) resolve.
- The "Knowledge Graph" / "PARA folders" / "Quick navigation" sections reflect current top-level structure.

If MEMORY.md has drifted, update it in place. The dashboard is the summary of current state; rebuilding it is trivial structural work.

**4. Classify findings.**

For each discrepancy from steps 1-3:
- **Trivial structural fix** (missing `INDEX.md` entry, frontmatter whitespace, inferrable `last_updated`, broken `related:` pointer with obvious replacement, MEMORY.md dashboard sections out of date): apply in place.
- **Anything else** (entity content, path, status semantics, ambiguous `related:` target, slug rename with downstream implications, new top-level folder): do NOT rewrite. Surface in the reply with file path, observed state, proposed fix. The operator decides.

## After processing

Single-run job. The cron is scheduled weekly; it fires, completes, and waits for next week. No self-disable; no queue to drain. A heartbeat-triggered mid-week run completes the same way.

## Commit

Add only the files you changed - never `git add -A`. Commit message: `para: align YYYY-Www - <summary>`. Push immediately after the commit. No AI attribution lines.

## Failure handling

If any step fails, the reply surfaces what failed and why. Do NOT attempt partial rewrites to work around structural problems. The operator resolves manually. The cron stays scheduled regardless.

## Reply

Single line summary. The runner announces it to the logs channel:

```
para-align YYYY-Www: verified <N> entities | trivial fixes <M> | proposals <K> (awaiting operator)
```

## What NOT to do

- Do not rewrite entity content for style or brevity.
- Do not move, rename, or delete files based on your own judgment; moves are operator decisions.
- Do not modify `AGENTS.md`, `HEARTBEAT.md`, or anything in `.openclaw/`.
- Do not disable or enable any cron.
- Do not auto-archive inactive projects (archive lifecycle is user-managed).

## Install

Prerequisite: `clawstodian/routines` symlink to `~/clawstodian/routines`.

```bash
openclaw cron add \
  --name para-align \
  --cron "0 6 * * 0" \
  --session isolated \
  --light-context \
  --announce --channel discord --to "channel:<your-logs-channel-id>" \
  --message "Read clawstodian/routines/para-align.md and execute."
```

Runs Sunday 06:00 UTC. Starts enabled. Substitute `--no-deliver` for silent runs.

## Verify

```bash
openclaw cron list | grep para-align
```

## Uninstall

```bash
openclaw cron remove para-align
```
