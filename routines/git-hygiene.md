# git-hygiene (routine)

Every 30 minutes, always enabled. Runs one commit-drift pass per the git-hygiene program.

## Program

`clawstodian/programs/git-hygiene.md` - follow the "Commit drift" behavior.

## Target

The current workspace working tree and its remote-tracking branch.

## Exec safety

- Never `git add -A` or `git add .`. Stage by exact path.
- Never `--no-verify`. If a pre-commit hook fails, fix the underlying issue and commit again.
- Never `git reset --hard`, `git clean -f`, or force-push without explicit operator confirmation.
- Never inline code through heredocs piped into shell interpreters.

## Worker discipline

- One pass per firing. No internal loops.
- Group dirty files into logical commits; one concern per commit.
- If the program's approval gates or escalation rules say "surface", do not commit; include in the run report.

## Run report

Single line delivered to the logs channel by the cron runner:

```
git-hygiene: <N> commits pushed | <M> awaiting operator decision
```

Return `NO_REPLY` when the tree was already clean, so no-change runs stay silent.
