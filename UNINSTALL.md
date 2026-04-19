# UNINSTALL.md

Full removal of clawstodian from a workspace. Follow the steps in order and confirm each with the operator before acting. This is a destructive operation on workspace config and cron state; there is no shortcut.

Principle: **co-uninstall, don't automate**. Show the operator what each step removes and wait for approval before continuing. Leave anything the operator might want to keep (templates, heartbeat trace) in place.

## Pre-flight

1. Confirm the operator wants a full uninstall, not just disabling cron jobs. Disabling is reversible; uninstall is not.
2. Confirm which workspace directory to operate on.
3. Check that `openclaw` CLI is available:
   ```bash
   openclaw --version && openclaw cron list >/dev/null
   ```

## Step 1 - Disable and remove cron routines

Disable first (stops future firings), then remove (deletes the job entry). `openclaw cron disable|rm` take a job id, not a name. Discover every clawstodian-flavored cron by looking at the job's `message` field (all clawstodian routines dispatch via `Read clawstodian/routines/<name>.md and execute`), then loop:

```bash
openclaw cron list --json | \
  jq -r '.jobs[] | select(.payload.message // "" | test("clawstodian/")) | .id' | \
  while read -r id; do
    openclaw cron disable "$id" 2>/dev/null
    openclaw cron rm "$id" 2>/dev/null
  done
```

Verify:

```bash
openclaw cron list --json | jq -r '.jobs[] | select(.payload.message // "" | test("clawstodian/")) | .name'
```

Should print nothing.

## Step 2 - Remove the workspace `clawstodian/` directory

The workspace `clawstodian/` holds three symlinks into the package (`programs`, `routines`, `scripts`). Removing the directory removes all three but leaves the package clone at `~/clawstodian` untouched.

```bash
rm -rf clawstodian
```

Run from the workspace root.

## Step 3 - Remove the clawstodian section from `AGENTS.md`

Delete everything between the opening and closing template markers inclusive:

```
<!-- template: clawstodian/agents <date> -->
...
<!-- /template: clawstodian/agents <date> -->
```

Historical rename: any marker starting with `clawstodian/` (not just `clawstodian/agents`) counts - treat them the same way.

If the operator removed the markers when they adopted the template, the clawstodian content is the section headed `## Workspace Maintainer (clawstodian)` plus the subsections below it down to and including `### Cross-program escalation rules`. Identify the span, confirm with the operator, then delete.

If `AGENTS.md` becomes empty after this, the operator can delete the file or keep it as a stub.

If the operator customized the clawstodian block (moved memory-and-navigation into a top-level section, merged escalation rules elsewhere), surface those customizations and let the operator decide what to strip.

## Step 4 - Remove the clawstodian section from `HEARTBEAT.md`

Same shape as Step 3. Delete everything between:

```
<!-- template: clawstodian/heartbeat <date> -->
...
<!-- /template: clawstodian/heartbeat <date> -->
```

Same historical-rename rule applies: any `clawstodian/` marker, not just `clawstodian/heartbeat`.

If the operator removed the markers, the clawstodian content is essentially the whole HEARTBEAT.md for most workspaces - delete the file or strip its orchestrator content entirely.

If `HEARTBEAT.md` becomes empty:

- Leave it alone - heartbeat responds `HEARTBEAT_OK` every tick when the file is empty or missing.
- Or delete it entirely if the workspace no longer uses the heartbeat feature.

## Step 5 - Revert heartbeat config

Edit `~/.openclaw/openclaw.json` (or `config.toml`). The operator chose the config values at install; reverting means restoring whatever stance they had before clawstodian.

Typical revert options:

- Set `agents.defaults.heartbeat.every` back to the operator's prior value, or remove the heartbeat block entirely to disable it.
- Reset `target` (and `to`) to the prior values, or to `target: "last"` / `target: "none"`.
- Reset `activeHours` to prior values.
- Reset `channels.defaults.heartbeat.showAlerts` / `showOk` / `useIndicator` to prior values.

clawstodian does NOT set `session`, `isolatedSession`, `lightContext`, `session.maintenance`, `agents.defaults.contextPruning`, `session.dmScope`, or `session.reset` at install time - those are either defaults or host-wide baseline choices. Do not touch them during uninstall.

**`tools.sessions.visibility`** - the install sets this to `"all"` so isolated cron sessions can observe other sessions' transcripts. If the operator had a different value before clawstodian (e.g. `"tree"`), offer to restore the prior value. If they had no value set, leaving `"all"` in place is harmless unless another agent on the same gateway expects tighter scoping; let the operator decide.

The heartbeat ran in the agent's main session, so there is no separate maintainer session to prune. If the operator wants to reset main-session history entirely, that is a separate, more invasive decision handled outside this uninstall flow.

Show the operator the exact diff before applying. Prefer letting the operator apply it themselves.

## Step 6 - (Optional) delete the package clone

If `~/clawstodian` is no longer needed by any workspace on this machine:

```bash
rm -rf ~/clawstodian
```

Only do this with explicit operator confirmation. Other workspaces on the same machine may still depend on the clone.

## What to leave alone

These outlive clawstodian and stay in the workspace unless the operator explicitly asks to remove them:

- **Reference templates** - `memory/para-structure.md`, `memory/daily-note-structure.md`, `MEMORY.md`, `memory/crons.md`. These are workspace conventions; PARA and daily-note conventions remain useful after clawstodian is gone.
- **Workspace state** - daily notes at `memory/YYYY-MM-DD.md`, PARA entities under `projects/` / `areas/` / `resources/` / `archives/`, and everything git-tracked. The uninstall does not touch content.
- **`memory/session-ledger.md`** - historical record of which sessions were classified and how far their transcripts were captured. If the operator ever reinstalls clawstodian or a successor, this file lets capture resume where it left off instead of re-processing every session. Keep.
- **`memory/heartbeat-trace.md`** - historical tick record. Keep or archive at the operator's discretion.
- **Git history** - commits made by routines remain part of the workspace's history.

## Verification after uninstall

Run these to confirm the removal:

```bash
# Cron jobs gone (any cron whose message dispatches clawstodian/)
leftover=$(openclaw cron list --json | jq -r '.jobs[] | select(.payload.message // "" | test("clawstodian/")) | .name')
[ -z "$leftover" ] && echo "OK  cron entries removed" || echo "FAIL cron entries remain: $leftover"

# Workspace symlinks gone
[ -e clawstodian/programs ] && echo "FAIL programs symlink still present" || echo "OK  programs symlink removed"
[ -e clawstodian/routines ] && echo "FAIL routines symlink still present" || echo "OK  routines symlink removed"
[ -e clawstodian/scripts  ] && echo "FAIL scripts symlink still present"  || echo "OK  scripts symlink removed"

# Section markers gone (any clawstodian/ marker form)
grep -qE '<!-- template: clawstodian/' AGENTS.md 2>/dev/null && echo "FAIL agents marker still present" || echo "OK  agents marker removed"
grep -qE '<!-- template: clawstodian/' HEARTBEAT.md 2>/dev/null && echo "FAIL heartbeat marker still present" || echo "OK  heartbeat marker removed"
```

All lines should print `OK`.

## Re-installing later

If the operator wants to reinstall clawstodian, follow `INSTALL.md`. The install flow detects existing state and proposes only the needed merges.
