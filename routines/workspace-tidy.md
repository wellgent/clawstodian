# workspace-tidy

Keep the working tree navigable. Remove trash, move misplaced files to their intuitive home, leave signal. Always-on cron.

## References

- Related routines -> `clawstodian/routines/git-hygiene.md`, `clawstodian/routines/para-extract.md`, `clawstodian/routines/para-align.md`
- PARA conventions -> `memory/para-structure.md`
- Dashboard -> `MEMORY.md`

## Authority

- Delete empty directories unless `.gitkeep` marks them intentional.
- Prune run-logs older than 30 days.
- Remove scratch files the agent itself created and no longer references.
- Move misplaced files to their intuitive location when the right home is obvious per `memory/para-structure.md`.
- Edit `.gitignore`.

## Trigger

Every 2 hours (see Install). Always-on cron; no heartbeat toggling. Quiet runs reply `NO_REPLY` to stay silent.

## Approval gates

- Obvious removal (empty dir, stale run-log, own scratch file): just do it.
- Obvious move (misplaced file with a clearly intuitive home per PARA conventions): just do it.
- Ask before removing anything the agent did not create or cannot trace the origin of.
- Ask before deleting files larger than 1 MB or any binary.
- Ask before touching a top-level directory not listed in `MEMORY.md` or the PARA folders.
- Ask before moving a file whose intended location is genuinely ambiguous (fits two PARA buckets, could be entity-owned or workspace-owned).

## Escalation

- Orphaned symlink pointing outside the workspace.
- Permission anomaly or a file mode that looks wrong.
- A file whose presence suggests a separate concern (a stray dataset, a possibly sensitive artifact).

Surface with filename and observed state; do not auto-repair.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

## What to do

1. Walk the workspace. Collect candidates in four buckets:
   - **Empty directories** (no `.gitkeep` sentinel).
   - **Stale artifacts** (run-logs older than 30 days, scratch files the agent created).
   - **Misplaced files** (files at workspace root that clearly belong under `resources/`, `projects/<n>/`, or another PARA bucket per `memory/para-structure.md`).
   - **Anomalies** (broken symlinks, oversized files, unknown-origin files).
2. For each candidate:
   - Obvious action (per authority and approval gates): apply.
   - Ambiguous: surface in the reply and leave alone.
3. Keep the tree clean: `.gitignore` patterns for any ephemeral files that slipped in.

## What NOT to do

- Do not reorganize operator-authored directory structure.
- Do not rename files.
- Do not touch `.git/`, `.openclaw/`, or any dotfile the operator configured.
- Do not trash anything produced by another routine without tracing origin first.
- Do not auto-archive inactive projects (archive lifecycle is user-managed).

## Reply

Single line summary. The runner announces it to the logs channel. Reply `NO_REPLY` on quiet runs:

```
workspace-tidy: removed <N>, moved <M>, awaiting decision on <K>
```

Or:

```
NO_REPLY
```

## Install

Prerequisite: `clawstodian/routines` symlink to `~/clawstodian/routines`.

```bash
openclaw cron add \
  --name workspace-tidy \
  --every 2h \
  --session isolated \
  --light-context \
  --announce --channel discord --to "channel:<your-logs-channel-id>" \
  --message "Read clawstodian/routines/workspace-tidy.md and execute."
```

Substitute `--no-deliver` for silent runs.

## Verify

```bash
openclaw cron list | grep workspace-tidy
```

## Uninstall

```bash
openclaw cron remove workspace-tidy
```
