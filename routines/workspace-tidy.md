# workspace-tidy (routine)

Every 2 hours, always enabled. Runs one tidy pass across the workspace per the workspace-tidy program.

## Program

`clawstodian/programs/workspace-tidy.md` - follow the "Walk and tidy" behavior.

## Target

The workspace tree, excluding `.git/`, `.openclaw/`, and operator-configured dotfiles.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

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

## Install

Prerequisite: `clawstodian/routines` and `clawstodian/programs` symlinks.

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
