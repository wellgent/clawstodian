# git-clean (routine)

Runs one commit-drift pass per the repo program.

## Program

`clawstodian/programs/repo.md` - follow the "Commit drift" behavior.

## Target

The current workspace working tree and its remote-tracking branch.

## Exec safety

- Never `git add -A` or `git add .`. Stage by exact path.
- Never `--no-verify`. If a pre-commit hook fails, fix the underlying issue and commit again.
- Never `git reset --hard`, `git clean -f`, or force-push without explicit operator confirmation.
- Run commands by exact path. No `eval`, `bash -c "..."`, or other indirection that hides the real command from the gateway's exec safety layer.
- For multi-line script logic, write the script to `/tmp/clawstodian-git-clean-<context>.sh` (or `.py`) and invoke it by path. Do not inline code via heredoc to an interpreter (`bash <<EOF ... EOF`); the safety layer blocks that as obfuscation.
- `jq` and `python3 -c '<short expression>'` one-liners are fine when they fit on one line and the intent is obvious.

## Worker discipline

- One pass per firing. No internal loops.
- Group dirty files into logical commits; one concern per commit.
- If the program's approval gates or escalation rules say "surface", do not commit; include in the run report.

## Run report

Two artifacts every firing: a full report on disk following the shared run-report shape, and a multi-line scannable summary posted to the notifications channel. Every firing produces both - no silent firings.

### File on disk

Write to `memory/runs/git-clean/<YYYY-MM-DD>T<HH-MM-SS>Z.md`.

```markdown
# git-clean run report

- timestamp: 2026-04-18T14:00:00Z
- context: 2026-04-18T14:00Z firing
- outcome: committed
- branch: main
- pushed: yes

## What happened

- commits made: 2
- pushed: yes

## Commits

- abc1234 memory: append 2026-04-18 notes on VPS migration
- def5678 projects/vps-migration: add provisioning steps

## Surfaced for operator

- 1
  - .env.new at workspace root - looks like secrets; ignored rather than committed. Operator to confirm.

## Channel summary

git-clean · 2026-04-18T14:00Z · committed
Commits: 2 pushed
Awaiting decision: 1
Report: memory/runs/git-clean/2026-04-18T14-00-00Z.md
```

### Channel summary

Multi-line. One insight per line:

**Meaningful firing:**

```
git-clean · <ISO timestamp UTC> · <outcome>
Commits: <N> pushed
Awaiting decision: <M>
Report: memory/runs/git-clean/<ts>.md
```

`outcome` is `committed | surfaced-only | failed`. Omit the "Awaiting decision" line when M is 0.

**Quiet firing** (tree already clean):

```
git-clean · <ISO timestamp UTC> · clean
Working tree clean · nothing to commit
Report: memory/runs/git-clean/<ts>.md
```

### Every firing speaks

Every firing produces both a run-report file and a channel post - including clean-tree firings where there was nothing to commit. The post confirms the cron is alive and the check actually ran. A three-line "clean" post is the minimum.
