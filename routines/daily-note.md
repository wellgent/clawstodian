# daily-note (routine)

Every 30 minutes, always enabled. Tends today's canonical daily note per the daily-notes program.

## Program

`clawstodian/programs/daily-notes.md` - follow the "Tend today's note" behavior.

## Target

`memory/YYYY-MM-DD.md` for today's workspace-local date.

## Exec safety

Run commands by exact path. Never inline code through heredocs piped into shell interpreters.

## Worker discipline

- One pass per firing. No internal loops.
- Stop after merging slug siblings, appending net-new activity, filing obvious insights, and updating frontmatter.
- If the program's approval gates say "surface", do not act.

## Run report

Single line delivered to the logs channel by the cron runner:

```
daily-note YYYY-MM-DD: appended <N> sections | merged <M> slug siblings | filed <K> insights | <L> awaiting operator
```

Return `NO_REPLY` when nothing changed, so no-change runs stay silent.

## Install

Prerequisite: `clawstodian/routines` symlink to `~/clawstodian/routines` and `clawstodian/programs` symlink to `~/clawstodian/programs`.

```bash
openclaw cron add \
  --name daily-note \
  --every 30m \
  --session isolated \
  --light-context \
  --announce --channel discord --to "channel:<your-logs-channel-id>" \
  --message "Read clawstodian/routines/daily-note.md and execute."
```

Substitute `--no-deliver` if the operator prefers silent runs.

## Verify

```bash
openclaw cron list | grep daily-note
```

## Uninstall

```bash
openclaw cron remove daily-note
```
