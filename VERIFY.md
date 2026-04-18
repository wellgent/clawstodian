# VERIFY.md

Standalone verification for a clawstodian install. Run these checks after the install flow finishes, after a gateway restart, after a package upgrade, or any time you want to confirm the setup is healthy.

Each check is a pass/fail line. Run them from the **workspace root** (the directory where `AGENTS.md` and `HEARTBEAT.md` live, and where `clawstodian/programs` and `clawstodian/routines` symlinks should resolve).

## Scope

Verify covers install correctness and current state:

- Section markers landed in `AGENTS.md` and `HEARTBEAT.md`.
- Both workspace symlinks (`clawstodian/programs`, `clawstodian/routines`) resolve.
- All four program specs reachable at `clawstodian/programs/<name>.md`.
- All six routine specs reachable at `clawstodian/routines/<name>.md`.
- All four reference templates installed under `memory/` and at workspace root.
- All six cron jobs registered (`openclaw cron list --all`).
- Heartbeat config matches the recommended stance.
- `memory/heartbeat-trace.md` exists (or will on first tick).

Verify does NOT check that routines are delivering work over time; that is a separate audit concern and deferred.

## Quick verify

Paste the whole block into a shell. Each line prints one pass/fail indicator.

```bash
# Template markers in place (or legacy markers from v0.3 / early v0.4)
grep -qE 'clawstodian/agents(-section)?' AGENTS.md 2>/dev/null && echo "OK  agents marker" || echo "FAIL agents marker"
grep -qE 'clawstodian/heartbeat(-section)?' HEARTBEAT.md 2>/dev/null && echo "OK  heartbeat marker" || echo "FAIL heartbeat marker"

# Reference templates present at workspace root
[ -f AGENTS.md ] && echo "OK  AGENTS.md present" || echo "FAIL AGENTS.md missing"
[ -f HEARTBEAT.md ] && echo "OK  HEARTBEAT.md present" || echo "FAIL HEARTBEAT.md missing"

# Workspace symlinks resolve
readlink -e clawstodian/programs >/dev/null 2>&1 && echo "OK  programs symlink" || echo "FAIL programs symlink"
readlink -e clawstodian/routines >/dev/null 2>&1 && echo "OK  routines symlink" || echo "FAIL routines symlink"

# Program specs reachable (four domain authorities)
for name in daily-notes para workspace-tidy git-hygiene; do
  [ -f "clawstodian/programs/${name}.md" ] && echo "OK  program ${name}" || echo "FAIL program ${name}"
done

# Routine specs reachable (six scheduled dispatchers)
for name in daily-note seal-past-days para-extract para-align workspace-tidy git-hygiene; do
  [ -f "clawstodian/routines/${name}.md" ] && echo "OK  routine ${name}" || echo "FAIL routine ${name}"
done

# Reference templates installed
for f in memory/para-structure.md memory/daily-note-structure.md MEMORY.md memory/crons.md; do
  [ -f "$f" ] && echo "OK  template ${f}" || echo "MISSING template ${f}"
done

# Cron jobs registered
for name in daily-note workspace-tidy git-hygiene para-align seal-past-days para-extract; do
  openclaw cron list --all 2>/dev/null | grep -q " ${name} " && echo "OK  cron ${name}" || echo "FAIL cron ${name}"
done

# Heartbeat trace file present (or prepare it for first tick)
[ -f memory/heartbeat-trace.md ] && echo "OK  heartbeat-trace" || { touch memory/heartbeat-trace.md && echo "OK  heartbeat-trace (created)"; }
```

Any `FAIL` should be investigated before relying on the install.

## Heartbeat config sanity check

The heartbeat lives in `~/.openclaw/openclaw.json` (or `config.toml`), not in the workspace. Read it and confirm:

- `agents.defaults.heartbeat.every` is set (recommended: `"2h"`).
- `agents.defaults.heartbeat.target` is set to the notifications channel id (not empty, not `"last"`).
- `agents.defaults.heartbeat.activeHours` has `start`, `end`, `timezone` - matches the operator's preferred window.
- `channels.defaults.heartbeat.showAlerts` is `true`.
- `agents.defaults.heartbeat.session`, `isolatedSession`, and `lightContext` are either omitted (defaults) or set to: no `session` override, `isolatedSession: false`, `lightContext: false`. These defaults mean heartbeat runs in the agent's main session with full workspace bootstrap.

A config that passes every other check but has `target: ""` or `showAlerts: false` will produce a silent heartbeat. That is the failure mode v0.4 is designed to prevent; catch it here.

**Not checked here:** `session.maintenance`, `agents.defaults.contextPruning`, `session.dmScope`, `session.reset`. These are host-wide policy choices from the operator's sessions baseline; clawstodian does not prescribe them.

`docs/heartbeat-config.md` has the full reference.

## Burst-worker enable state

Burst workers (`seal-past-days`, `para-extract`) are expected to be **disabled at install time**. The heartbeat enables them on demand when a queue appears.

```bash
openclaw cron list --all | grep -E " (seal-past-days|para-extract) "
```

Both should show as disabled right after install. If they are enabled with no queue, the heartbeat's first tick will disable them automatically (safe but noisy).

## Recent heartbeat evidence (optional, after first tick)

After the first real heartbeat tick fires:

```bash
tail -n 5 memory/heartbeat-trace.md
```

Each line is a tick record in the shape:

```
YYYY-MM-DDTHH:MM:SSZ | seal=<0|1> extract=<0|1> | enabled: <routines toggled> | health: <ok|anomaly:reason> | summary: <one-line>
```

If `memory/heartbeat-trace.md` is still empty long after install, the heartbeat is not firing. Check:

- Gateway is running.
- Heartbeat config is enabled and within `activeHours`.
- Delivery target channel is reachable.

The orchestrator is designed to **never be silent**; empty trace plus no channel posts means something upstream is broken.

## When to re-run VERIFY

- After running the install flow in `INSTALL.md`.
- After upgrading the clawstodian package (`git pull` in `~/clawstodian`).
- After a gateway restart, if heartbeat posts stop appearing in the logs channel.
- After an operator-initiated config change to `~/.openclaw/openclaw.json`.
- Any time something feels off.

Verify is cheap and idempotent. Run it often.
