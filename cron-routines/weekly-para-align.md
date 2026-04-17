# weekly-para-align

Verify PARA structural integrity for the current ISO week. Surface drift; do not rewrite entity content. Runs once per week; no queue, no self-disable.

## References

- PARA conventions -> `memory/para-structure.md`
- Workspace dashboard -> `MEMORY.md` at workspace root

Read `memory/para-structure.md` before starting. It defines the conventions you are validating against.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters; the gateway's exec safety layer blocks that as obfuscation.

## What to do

**1. Walk the graph.**

For each entity file in `projects/`, `areas/`, `resources/`, `archives/`:
- Frontmatter matches `memory/para-structure.md` (required common fields, type-specific fields, valid status values).
- `related:` pointers resolve to existing files.
- The entity is listed in the relevant `INDEX.md`.

**2. Verify `MEMORY.md`.**

- Every project with `status: active` is individually listed.
- Retired projects are not listed under active.
- Infrastructure pointers resolve.

**3. Classify findings.**

For each discrepancy:
- **Trivial structural fix** (missing `INDEX.md` entry, frontmatter whitespace, obviously-inferable `last_updated`): apply in place.
- **Anything else** (entity content, path, status, `related:` pointers, entity renames): do NOT rewrite. Surface in the reply with file path, observed state, proposed fix. The operator decides.

## After processing

Single-run job. The cron is scheduled weekly; it fires, completes, and waits for next week. No self-disable; no queue to drain.

## Commit

Add only the files you changed - never `git add -A`. Commit message: `para: weekly align YYYY-Www - <summary>`. No AI attribution lines.

## Failure handling

If any step fails, the reply surfaces what failed and why. Do NOT attempt partial rewrites to work around structural problems. The operator resolves manually or during the next heartbeat `workspace-sweep`. The cron stays enabled for next week regardless.

## Reply

Single line summary to the session:

```
weekly-para-align YYYY-Www: verified N | trivial fixes M | proposals K (awaiting operator)
```

## What NOT to do

- Do not rewrite entity content for style or brevity.
- Do not move, rename, or delete files.
- Do not modify `AGENTS.md`, `HEARTBEAT.md`, or anything in `.openclaw/`.
- Do not disable or enable any cron.

## Install

Prerequisite: the workspace has a `clawstodian/` directory with symlinks to the package's `cron-routines/*.md` files. `INSTALL_FOR_AGENTS.md` creates this during setup; if you are adding this routine later, create the symlink first:

```bash
mkdir -p clawstodian
ln -sf ~/clawstodian/cron-routines/weekly-para-align.md clawstodian/weekly-para-align.md
```

Register the cron:

```bash
openclaw cron add \
  --name weekly-para-align \
  --cron "0 6 * * 0" \
  --session isolated \
  --light-context \
  --no-deliver \
  --message "Read clawstodian/weekly-para-align.md and execute."
```

Runs Sunday 06:00 in the host's local timezone. Starts enabled (unlike `close-of-day`, this is a plain scheduled job - no demand-driven toggling).

## Verify

```bash
openclaw cron list | grep weekly-para-align
```

## Uninstall

```bash
openclaw cron remove weekly-para-align
```
