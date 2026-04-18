# workspace-tidy (routine)

Runs one tidy pass across the workspace per the workspace-tidy program.

## Program

`clawstodian/programs/workspace-tidy.md` - follow the "Walk and tidy" behavior.

## Target

The workspace tree, excluding `.git/`, `.openclaw/`, and operator-configured dotfiles.

## Exec safety

- Run commands by exact path. No `eval`, `bash -c "..."`, or other indirection that hides the real command from the gateway's exec safety layer.
- For multi-line script logic, write the script to `/tmp/clawstodian-tidy-<context>.py` (or `.sh`) and invoke it by path. Do not inline code via heredoc to an interpreter (`python3 <<EOF ... EOF`); the safety layer blocks that as obfuscation.
- `jq` and `python3 -c '<short expression>'` one-liners are fine when they fit on one line and the intent is obvious.

## Worker discipline

- One pass per firing. No internal loops.
- Apply only the obvious actions the program authorizes. Everything ambiguous surfaces in the run report.
- Do not commit. Commits belong to the `git-hygiene` routine.

## Run report

Two artifacts on firings that changed anything: a full report on disk following the shared run-report shape, and a multi-line scannable summary posted to the notifications channel. On truly quiet firings: `NO_REPLY` (no file, no channel post).

### File on disk

Write to `memory/runs/workspace-tidy/<YYYY-MM-DD>T<HH-MM-SS>Z.md`.

```markdown
# workspace-tidy run report

- timestamp: 2026-04-18T10:00:00Z
- context: 2026-04-18T10:00Z firing
- outcome: tidied

## What happened

### Removed

- 3
  - .DS_Store (workspace root)
  - tmp/stale-scratch-2026-03-01/
  - .firecrawl/release-watch-2026-04-13/scrapes/*.html (expired)

### Moved

- 1
  - random-thought.md → resources/random-thought.md

## Commits

- (none - workspace-tidy does not commit; git-hygiene picks up the changes)

## Surfaced for operator

- 2
  - foo.draft.md at workspace root - unclear whether resource or scratch
  - archives/old-project/ - should this move to archives or be deleted?

## Channel summary

workspace-tidy · 2026-04-18T10:00Z · tidied
Removed: 3 · moved: 1
Awaiting decision: 2
Report: memory/runs/workspace-tidy/2026-04-18T10-00-00Z.md
```

### Channel summary

Multi-line. One insight per line:

```
workspace-tidy · <ISO timestamp UTC> · <outcome>
Removed: <N> · moved: <M>
Awaiting decision: <K>
Report: memory/runs/workspace-tidy/<ts>.md
```

- `outcome` is `tidied | surfaced-only | failed`.
- Omit the "Awaiting decision" line when K is 0.

Return `NO_REPLY` on no-change firings (removed=0, moved=0, surfaced=0). No file is written in that case.
