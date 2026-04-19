# workspace

Governs the workspace tree itself - everything outside PARA that keeps the tree navigable: trash is removed, misplaced files land in their intuitive home, ephemeral artifacts are `.gitignore`d, and the tree is intuitive to scan for both the operator and any agent working in it.

The goal is a workspace with no files or directories that have outlived their purpose, and no files living where a future reader would not expect to find them. The program detects candidates; the operator decides on anything it did not create itself.

## Who tends

**In-session agents are the primary tenders.** Any agent noticing an obviously-stale scratch file, a misplaced artifact, or a directory that should have been `.gitignore`d acts on it per the conventions below. This is the default path.

Under cron, `workspace-clean` runs a weekly walk to catch what in-session work left behind and to surface suspicion about stale or misplaced top-level content (and orphaned-looking dotfiles) for operator decision.

## References

- PARA conventions (for deciding a file's intuitive home) -> `memory/para-structure.md`
- Workspace dashboard -> `MEMORY.md`
- Related programs -> `clawstodian/programs/repo.md` (commits the changes this program produces)

## Conventions

- **Trash**: empty directories without `.gitkeep`, run-report files under `memory/runs/<routine>/` older than 30 days, scratch files the agent created and no longer references, broken symlinks. The run-report directories themselves (`memory/runs/<routine>/`) always stay; only files older than 30 days inside them get pruned.
- **Misplaced files**: files at workspace root that belong under `resources/`, `projects/<name>/`, or another PARA bucket per `memory/para-structure.md`.
- **Stale top-level content**: files or directories at workspace root not referenced in `MEMORY.md` navigation and not part of a known PARA bucket or infrastructure directory, that appear to have outlived their purpose (stale mtime, no recent git activity, no referrers).
- **Orphaned dotfiles**: workspace-root dotfiles (excluding `.git/`, `.openclaw/`, and operator-configured ones referenced in `README.md` / `MEMORY.md`) whose referenced tool or workflow no longer has an obvious current owner in the workspace.
- **Anomalies**: broken symlinks, oversized files in unexpected places, unknown-origin files, permission outliers.
- **Operator judgment required.** Stale top-level content, orphaned dotfiles, misplaced files whose home is ambiguous, and anomalies are surfaced for operator decision. The program detects and surfaces; it does not delete or rename operator-authored structure on its own.
- **Archive lifecycle is user-managed.** Actual moves of inactive projects or resources into `archives/` are operator decisions; this program does not auto-archive. Archive candidacy recommendations (which entities look inactive enough to consider archiving) are detected and surfaced by the PARA program (see `clawstodian/programs/para.md` and `clawstodian/routines/para-align.md`), not by this program.

## Authority

- Delete empty directories (no `.gitkeep`).
- Prune run-report files older than 30 days under `memory/runs/<routine>/`. Never delete the per-routine directories themselves, only aged files inside.
- Remove scratch files the agent itself created and no longer references.
- Move misplaced files to their intuitive location when the right home is obvious per `memory/para-structure.md` (e.g. a `<project-slug>-notes.md` at root when `projects/<project-slug>/` already exists).
- Edit `.gitignore` to cover ephemeral patterns that slipped in.
- Surface suspicion on any stale-looking or misplaced top-level file / directory / orphaned-looking dotfile, with file path, observed state, and a one-line reasoning.

Must NOT delete or rename operator-authored files or directories unilaterally. Must NOT touch `.git/`, `.openclaw/`, or dotfile contents. Surfacing suspicion about a dotfile is allowed and encouraged; modifying or deleting one is not.

## Approval gates

- **Obvious action -> act.** Empty dir, aged run-report, own scratch file, a misplaced file with a clearly intuitive home.
- **Surface otherwise.** Anything the agent did not create or cannot trace origin of; files larger than 1 MB or any binary; a top-level directory not listed in `MEMORY.md` or PARA folders; a file whose intended location is genuinely ambiguous (fits two PARA buckets); a dotfile whose reason-to-exist is not obvious.

## Escalation

- Orphaned symlink pointing outside the workspace.
- Permission anomaly or a file mode that looks wrong.
- A file whose presence suggests a separate concern (a stray dataset, a possibly sensitive artifact).

Surface with filename and observed state; do not auto-repair.

## What NOT to do

- Do not delete or rename operator-authored files or directories unilaterally; surface instead.
- Do not reorganize operator-authored directory structure.
- Do not modify or delete dotfiles; surfacing suspicion is the only allowed action on them.
- Do not touch `.git/` or `.openclaw/` at all.
- Do not trash anything produced by another program or routine without tracing origin first.
- Do not auto-archive inactive projects.
- Do not commit. Commits belong to the `repo` program.
