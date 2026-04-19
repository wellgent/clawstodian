# workspace-clean (routine)

Runs one walk per firing: sweeps obvious trash, moves clearly-misplaced files to their PARA home, and surfaces suspicion about stale top-level content, orphaned-looking dotfiles, and anomalies for operator decision. Detection-heavy; unilateral deletion is limited to what the agent itself owns or what is clearly aged.

## Program

`clawstodian/programs/workspace.md` - conventions, authority, approval gates, and escalation.

## Target

The full workspace tree. `.git/` and `.openclaw/` are skipped entirely; all other top-level content (including dotfiles) is walked.

## Steps

1. **Sweep trash.** Apply in place (trivial actions per the program's Authority):
   - Files under `memory/runs/<routine>/` older than 30 days. Never delete the per-routine directories themselves.
   - Empty directories without `.gitkeep`.
   - Broken symlinks.
   - Scratch files the agent itself created and no longer references.

2. **Reconcile root against MEMORY.md and PARA.** Walk the workspace root. For each top-level entry that is not known infrastructure (`projects/`, `areas/`, `resources/`, `archives/`, `memory/`, `README.md`, `AGENTS.md`, `HEARTBEAT.md`, `MEMORY.md`, `.git/`, `.openclaw/`, anything referenced in `MEMORY.md` navigation):
   - **File with a clearly intuitive PARA home** (e.g. `vps-migration-notes.md` at root when `projects/vps-migration/` exists): move in place. Record in the "Moved" section.
   - **File or directory without an obvious home and no recent-activity signal** (not mentioned in recent daily notes, no recent `git log` touches, nothing pointing to it from `MEMORY.md`): surface as stale top-level content. Do NOT delete.
   - **Anything ambiguous** (could fit two PARA buckets, unclear origin): surface. Do NOT move or delete.

3. **Audit dotfiles.** Enumerate workspace-root dotfiles (`.<name>`), excluding `.git/`, `.openclaw/`, and any dotfile referenced in `README.md` or `MEMORY.md`. For each:
   - **Obvious current purpose** (recent mtime, referenced by a known workflow, part of a standard toolchain config the operator uses): skip.
   - **Orphaned-looking** (stale mtime, pattern suggesting a one-off backup or experiment, no evident current owner): surface with path, size, and mtime. Do NOT read or paste contents into the run report; do NOT delete. The operator reviews directly.

4. **Anomaly sweep.** Scan for:
   - Files >1 MB at unexpected locations.
   - Binary files outside known buckets.
   - Files with permission outliers (world-writable, setuid, etc.).
   - Symlinks pointing outside the workspace.
   Surface each with path and observed state. Never auto-repair.

5. **`.gitignore` hygiene.** For any ephemeral pattern discovered during the walk (cache dir, build artifact, editor swapfile): add to `.gitignore`. The next `git-clean` firing picks up the change and commits it.

## Exec safety

- Run commands by exact path. No `eval`, `bash -c "..."`, or other indirection that hides the real command from the gateway's exec safety layer.
- For multi-line script logic, write the script to `/tmp/clawstodian-workspace-clean-<context>.py` (or `.sh`) and invoke it by path. Do not inline code via heredoc to an interpreter (`python3 <<EOF ... EOF`); the safety layer blocks that as obfuscation.
- `jq` and `python3 -c '<short expression>'` one-liners are fine when they fit on one line and the intent is obvious.

## Worker discipline

- One pass per firing. No internal loops.
- Apply only the trivial actions the program authorizes (trash sweep, aged-report prune, obvious PARA move, `.gitignore` patterns). Everything else is surface-only.
- Detection steps (root reconciliation, dotfile audit, anomaly sweep) are read-only. Never delete or rename operator-authored content from inference.
- Do not read dotfile contents into the report; path, size, and mtime are sufficient for surfacing.
- Do not commit. Commits belong to the `git-clean` routine.

## Run report

Two artifacts every firing: a full report on disk following the shared run-report shape, and a multi-line scannable summary posted to the notifications channel. Every firing produces both - no silent firings.

### File on disk

Write to `memory/runs/workspace-clean/<YYYY-MM-DD>T<HH-MM-SS>Z.md`.

```markdown
# workspace-clean run report

- timestamp: 2026-04-18T10:00:00Z
- context: 2026-04-18T10:00Z firing
- outcome: tidied

## What happened

### Removed

- 4
  - tmp/stale-scratch-2026-03-01/ (empty directory)
  - memory/runs/sessions-capture/2026-03-10T03-00-00Z.md (>30 days)
  - memory/runs/git-clean/2026-03-12T01-00-00Z.md (>30 days)
  - broken-link -> /var/old/path (broken symlink)

### Moved

- 1
  - vps-migration-notes.md → projects/vps-migration/notes.md (root -> project)

### Root reconciliation

- top-level entries reviewed: 24
- stale-content candidates: 2
  - experiments/ - directory last touched 2025-08-20, not in MEMORY.md navigation, no referrers
  - foo.draft.md - root file, last mtime 2025-11-02, unclear whether resource or scratch

### Dotfile audit

- dotfiles scanned: 12
- orphaned candidates: 1
  - .vimrc.bak - 2 KB, mtime 2025-10-04, looks like a one-off backup with no referring config

### Anomalies

- (none)

### `.gitignore` additions

- 1
  - `node_modules/` (found at workspace root; leaving the commit to git-clean)

## Commits

- (none - workspace-clean does not commit; git-clean picks up the changes)

## Surfaced for operator

- 3 items (details in the subsections above)
  - experiments/ - stale top-level directory; clean up, move, or keep?
  - foo.draft.md - ambiguous root file; resource or scratch?
  - .vimrc.bak - orphaned-looking dotfile; delete, keep, or move?

## Channel summary

workspace-clean · 2026-04-18T10:00Z · tidied
Removed: 4 · moved: 1
Surfaced: 2 stale · 1 orphaned dotfile · 0 anomalies
Report: memory/runs/workspace-clean/2026-04-18T10-00-00Z.md
```

### Channel summary

Multi-line. One insight per line:

**Meaningful firing:**

```
workspace-clean · <ISO timestamp UTC> · <outcome>
Removed: <N> · moved: <M>
Surfaced: <S1> stale · <S2> orphaned dotfiles · <S3> anomalies
Report: memory/runs/workspace-clean/<ts>.md
```

- `outcome` is `tidied | surfaced-only | failed`. `surfaced-only` covers a firing where the walk was clean of trash but detection surfaced at least one candidate.
- Omit the "Surfaced" line when S1 + S2 + S3 is 0.

**Quiet firing** (walk found nothing at all):

```
workspace-clean · <ISO timestamp UTC> · clean
Nothing to tidy · nothing surfaced
Report: memory/runs/workspace-clean/<ts>.md
```

### Every firing speaks

Every firing produces both a run-report file and a channel post - including clean firings where the walk found nothing. The post confirms the cron is alive and the walk actually happened. A three-line "clean" post is the minimum.
