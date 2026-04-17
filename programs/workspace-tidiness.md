# workspace-tidiness

Keep the working tree navigable. Remove trash, leave signal. Heartbeat-direct: typically ticks in the same pass as `git-hygiene` and `health-sweep`.

## References

- Related programs (same tick) -> `clawstodian/programs/git-hygiene.md`, `clawstodian/programs/health-sweep.md`
- PARA dashboard -> `MEMORY.md`

## Authority

- Delete empty directories unless `.gitkeep` marks them intentional.
- Prune run-logs older than 30 days.
- Remove scratch files the agent itself created and no longer references.
- Edit `.gitignore`.

## Trigger

Heartbeat task `workspace-sweep` on interval, folded with `git-hygiene` and `health-sweep`.

## Approval gates

- Ask before removing anything the agent did not create or cannot trace the origin of.
- Ask before deleting files larger than 1 MB or any binary.
- Ask before touching a top-level directory not listed in `MEMORY.md` or the PARA folders.

## Escalation

- Orphaned symlink pointing outside the workspace.
- Permission anomaly or a file mode that looks wrong.

Surface with the filename and observed state; do not auto-repair.

## What to do

1. Walk the workspace looking for: empty directories, stale run-logs, scratch files with no references, broken symlinks, oversized files in unexpected places.
2. For each finding: obvious action -> do it; not obvious -> queue for the tick's signalling batch.
3. After the pass, report a one-line summary: `tidied N items, awaiting decision on M`.

## What NOT to do

- Do not reorganize operator-authored directory structure.
- Do not rename files.
- Do not touch `.git/`, `.openclaw/`, or any dotfile the operator configured.
- Do not trash anything produced by a program outside this one without tracing origin first.
