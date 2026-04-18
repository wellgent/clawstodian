# workspace-clean (routine)

Runs one walk-and-tidy pass across the workspace per the workspace program.

## Program

`clawstodian/programs/workspace.md` - follow the "Walk and tidy" behavior.

## Target

The workspace tree, excluding `.git/`, `.openclaw/`, and operator-configured dotfiles.

## Exec safety

- Run commands by exact path. No `eval`, `bash -c "..."`, or other indirection that hides the real command from the gateway's exec safety layer.
- For multi-line script logic, write the script to `/tmp/clawstodian-workspace-clean-<context>.py` (or `.sh`) and invoke it by path. Do not inline code via heredoc to an interpreter (`python3 <<EOF ... EOF`); the safety layer blocks that as obfuscation.
- `jq` and `python3 -c '<short expression>'` one-liners are fine when they fit on one line and the intent is obvious.

## Worker discipline

- One pass per firing. No internal loops.
- Apply only the obvious actions the program authorizes. Everything ambiguous surfaces in the run report.
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

- 3
  - .DS_Store (workspace root)
  - tmp/stale-scratch-2026-03-01/
  - .firecrawl/release-watch-2026-04-13/scrapes/*.html (expired)

### Moved

- 1
  - random-thought.md → resources/random-thought.md

## Commits

- (none - workspace-clean does not commit; git-clean picks up the changes)

## Surfaced for operator

- 2
  - foo.draft.md at workspace root - unclear whether resource or scratch
  - archives/old-project/ - should this move to archives or be deleted?

## Channel summary

workspace-clean · 2026-04-18T10:00Z · tidied
Removed: 3 · moved: 1
Awaiting decision: 2
Report: memory/runs/workspace-clean/2026-04-18T10-00-00Z.md
```

### Channel summary

Multi-line. One insight per line:

**Meaningful firing:**

```
workspace-clean · <ISO timestamp UTC> · <outcome>
Removed: <N> · moved: <M>
Awaiting decision: <K>
Report: memory/runs/workspace-clean/<ts>.md
```

`outcome` is `tidied | surfaced-only | failed`. Omit the "Awaiting decision" line when K is 0.

**Quiet firing** (walk found nothing):

```
workspace-clean · <ISO timestamp UTC> · clean
Nothing to tidy
Report: memory/runs/workspace-clean/<ts>.md
```

### Every firing speaks

Every firing produces both a run-report file and a channel post - including clean firings where the walk found nothing. The post confirms the cron is alive and the walk actually happened. A three-line "clean" post is the minimum.
