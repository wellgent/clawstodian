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

Single line delivered to the logs channel by the cron runner:

```
workspace-tidy: removed <N>, moved <M>, awaiting decision on <K>
```

Return `NO_REPLY` when nothing changed, so no-change runs stay silent.
