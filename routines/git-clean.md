# git-clean (routine)

Runs one commit-drift pass per firing - stages and commits unpushed changes to the working tree per the repo program's conventions. Backstop for in-session agents and other routines that produced file changes but did not commit.

## Program

`clawstodian/programs/repo.md` - conventions, authority, approval gates, and escalation.

## Target

The current workspace working tree and its remote-tracking branch.

## Steps

1. **Run `git status`.** If the tree is clean and no commits are waiting to be pushed, emit the quiet-firing channel post and stop.
2. **Push first if the only work is unpushed commits.** `git status` reports a clean tree but `git log @{u}..HEAD` shows commits: push them, then stop.
3. **Group dirty files into logical commits.** Walk `git status --porcelain` and `git diff` output and cluster into a small set of topic-coherent commits. Useful axes, combined as needed:

   - **Role** - workspace charter (`AGENTS.md`, `HEARTBEAT.md`, `MEMORY.md`, `memory/*-structure.md`, `memory/crons.md`), daily notes (`memory/YYYY-MM-DD*.md`), PARA entities (`projects/`, `areas/`, `resources/`, `archives/`), run reports (`memory/runs/<routine>/`), state files (`memory/session-ledger.md`, `memory/heartbeat-trace.md`), config / install artifacts (`.gitignore`, `clawstodian/` symlinks).
   - **Topic** - when one work unit touches multiple roles (e.g. a project kickoff that creates `projects/foo/`, updates `MEMORY.md`, and mentions foo in today's note), one topic-scoped commit captures the unit better than splitting by role.
   - **Time window** - a historical mass-edit (e.g. a format upgrade touching dozens of past daily notes) goes in one commit, separate from today's note edits.

   Aim for a handful of commits that each tell a story - typically 2-6 on a dirty-tree firing. One giant commit of many mixed files is too coarse; a commit per file is too fine. If no axis clusters the tree cleanly (genuinely mixed, unrelated changes with no theme), surface the tree in the run report and let the operator direct rather than guessing.
4. **For each group, in order:**
   - Stage files by exact path. Never `git add -A` or `git add .`.
   - Compose a commit message per the `<topic>: <short description>` convention in `programs/repo.md`.
   - Commit and push immediately. If push fails, surface the error and stop (do not keep committing behind a failed push).
5. **Handle new untracked files.** For each:
   - **Clearly ephemeral** (cache, build output, log, editor swapfile): add to `.gitignore`, commit the `.gitignore` change with a `config:` or `ops:` topic, push.
   - **Looks like a secret** (`.env*`, `*.key`, `credentials*`, tokens): surface. Never commit, never add to `.gitignore` without operator direction.
   - **Nature not obvious**: surface rather than committing or ignoring. Let the operator decide.

## Exec safety

- Run commands by exact path. No `eval`, `bash -c "..."`, or other indirection that hides the real command from the gateway's exec safety layer.
- For multi-line script logic, write the script to `/tmp/clawstodian-git-clean-<context>.sh` (or `.py`) and invoke it by path. Do not inline code via heredoc to an interpreter (`bash <<EOF ... EOF`); the safety layer blocks that as obfuscation.
- `jq` and `python3 -c '<short expression>'` one-liners are fine when they fit on one line and the intent is obvious.

## Worker discipline

- One pass per firing. No internal loops after the initial grouping.
- If approval gates or escalation rules in `programs/repo.md` say "surface", do not commit; include in the run report.
- Do not accumulate commits behind a failed push. Stop at the first push failure and surface.

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
  - .env.new at workspace root - looks like secrets; left untouched (not committed, not added to .gitignore). Operator to decide whether to keep, rename, or gitignore.

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
