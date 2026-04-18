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
