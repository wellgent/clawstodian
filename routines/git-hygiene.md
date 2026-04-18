# git-hygiene (routine)

Runs one commit-drift pass per the git-hygiene program.

## Program

`clawstodian/programs/git-hygiene.md` - follow the "Commit drift" behavior.

## Target

The current workspace working tree and its remote-tracking branch.

## Exec safety

- Never `git add -A` or `git add .`. Stage by exact path.
- Never `--no-verify`. If a pre-commit hook fails, fix the underlying issue and commit again.
- Never `git reset --hard`, `git clean -f`, or force-push without explicit operator confirmation.
- Run commands by exact path. No `eval`, `bash -c "..."`, or other indirection that hides the real command from the gateway's exec safety layer.
- For multi-line script logic, write the script to `/tmp/clawstodian-git-<context>.sh` (or `.py`) and invoke it by path. Do not inline code via heredoc to an interpreter (`bash <<EOF ... EOF`); the safety layer blocks that as obfuscation.
- `jq` and `python3 -c '<short expression>'` one-liners are fine when they fit on one line and the intent is obvious.

## Worker discipline

- One pass per firing. No internal loops.
- Group dirty files into logical commits; one concern per commit.
- If the program's approval gates or escalation rules say "surface", do not commit; include in the run report.

## Run report

On firings that committed or surfaced anything: a full report on disk plus a one-line summary to the notifications channel. On clean-tree firings: `NO_REPLY`, no file, no channel post.

### File on disk

Write to `memory/runs/git-hygiene/<YYYY-MM-DD>T<HH-MM-SS>Z.md` when there was work.

File shape:

```markdown
# git-hygiene run report

- timestamp: 2026-04-18T14:00:00Z
- outcome: committed | surfaced-only | failed
- branch: main
- pushed: yes

## Commits

- 2
  - <hash short> memory: append 2026-04-18 notes on VPS migration
  - <hash short> projects/vps-migration: add provisioning steps

## Awaiting operator decision (surfaced, not committed)

- 1
  - .env.new at workspace root - looks like secrets; ignored rather than committed. Operator to confirm.

## Channel summary

git-hygiene: 2 commits pushed | 1 awaiting operator decision | report: memory/runs/git-hygiene/2026-04-18T14-00-00Z.md
```

### Channel summary

```
git-hygiene: <N> commits pushed | <M> awaiting operator decision | report: memory/runs/git-hygiene/<ts>.md
```

Return `NO_REPLY` when the tree was already clean. No file is written in that case.
