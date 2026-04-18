# workspace

Governs the workspace tree itself - everything outside PARA that keeps the tree navigable: trash is removed, misplaced files land in their intuitive home, ephemeral artifacts are `.gitignore`d, and the tree is intuitive to scan for both the operator and any agent working in it.

## References

- PARA conventions (for deciding a file's intuitive home) -> `memory/para-structure.md`
- Workspace dashboard -> `MEMORY.md`
- Related programs -> `clawstodian/programs/repo.md` (commits the changes this program produces)

## Conventions

- **Trash categories**: empty directories without `.gitkeep`, run-report files under `memory/runs/<routine>/` older than 30 days, scratch files the agent created and no longer references, broken symlinks. The run-report directories themselves (`memory/runs/<routine>/`) always stay; only files older than 30 days inside them get pruned.
- **Misplaced files**: files at workspace root that belong under `resources/`, `projects/<name>/`, or another PARA bucket per `memory/para-structure.md`.
- **Anomalies**: broken symlinks, oversized files in unexpected places, unknown-origin files, permission outliers.
- **Operator territory**: top-level directories not listed in `MEMORY.md` or the PARA folders; dotfiles the operator configured; anything in `.git/`, `.openclaw/`.
- **Archive lifecycle is user-managed.** When inactive projects or resources move from live PARA into `archives/` stays an operator judgment call; this program does not auto-archive.

## Authority

- Delete empty directories (no `.gitkeep`).
- Prune run-report files older than 30 days under `memory/runs/<routine>/`. Never delete the per-routine directories themselves, only aged files inside.
- Remove scratch files the agent itself created and no longer references.
- Move misplaced files to their intuitive location when the right home is obvious per `memory/para-structure.md`.
- Edit `.gitignore` to cover ephemeral patterns that slipped in.

Must NOT reorganize operator-authored structure, rename operator-authored files, or touch dotfile configurations.

## Approval gates

- **Obvious action -> act.** Empty dir, stale run-log, own scratch file, a misplaced file with a clearly intuitive home.
- **Surface otherwise.** Anything the agent did not create or cannot trace origin of, files larger than 1 MB or any binary, a top-level directory not listed in `MEMORY.md` or PARA folders, a file whose intended location is genuinely ambiguous (fits two PARA buckets).

## Escalation

- Orphaned symlink pointing outside the workspace.
- Permission anomaly or a file mode that looks wrong.
- A file whose presence suggests a separate concern (a stray dataset, a possibly sensitive artifact).

Surface with filename and observed state; do not auto-repair.

## Behaviors

### Walk and tidy

1. Walk the workspace. Collect candidates in four buckets:
   - **Empty directories** (no `.gitkeep` sentinel).
   - **Stale artifacts** (run-report files at `memory/runs/<routine>/*` older than 30 days; scratch files the agent created).
   - **Misplaced files** (files at workspace root that clearly belong under a PARA bucket per `memory/para-structure.md`).
   - **Anomalies** (broken symlinks, oversized files, unknown-origin files).
2. For each candidate:
   - Obvious action (per Authority and Approval gates) -> apply.
   - Ambiguous -> surface and leave alone.
3. Keep the tree clean: add `.gitignore` patterns for any ephemeral files that slipped in.

## What NOT to do

- Do not reorganize operator-authored directory structure.
- Do not rename operator-authored files.
- Do not touch `.git/`, `.openclaw/`, or any dotfile the operator configured.
- Do not trash anything produced by another program or routine without tracing origin first.
- Do not auto-archive inactive projects.
- Do not commit. Commits belong to the `repo` program.
