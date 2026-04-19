# VERIFY.md

Standalone verification for a clawstodian install. Run these checks after the install flow finishes, after a gateway restart, after a package upgrade, or any time you want to confirm the setup is healthy.

Each check is a pass/fail line. Run them from the **workspace root** (the directory where `AGENTS.md` and `HEARTBEAT.md` live, and where `clawstodian/programs`, `clawstodian/routines`, and `clawstodian/scripts` symlinks should resolve).

## Scope

Verify covers install correctness and current state:

- Section markers landed in `AGENTS.md` and `HEARTBEAT.md`.
- All three workspace symlinks (`clawstodian/programs`, `clawstodian/routines`, `clawstodian/scripts`) resolve.
- All four program specs reachable at `clawstodian/programs/<name>.md`.
- All seven routine specs reachable at `clawstodian/routines/<name>.md`.
- `clawstodian/scripts/scan-sessions.py` is executable.
- All five reference templates installed under `memory/` and at workspace root.
- All seven cron jobs registered (`openclaw cron list --all`).
- Heartbeat config matches the recommended stance.
- `tools.sessions.visibility: "all"` is set (required for session capture).
- `memory/heartbeat-trace.md` exists (or will on first tick).
- `memory/session-ledger.md` exists (daily-notes authoritative capture-state file).

Verify does NOT check that routines are delivering work over time; ongoing machinery sanity (cron registrations, stalled routines, long-running bursts, symlinks, template markers) is covered by the `health-check` routine which fires daily once installed.

## Quick verify

Paste the whole block into a shell. Each line prints one pass/fail indicator.

```bash
# Template markers present (any clawstodian/ marker form; the install-currency check in health-check compares dates)
grep -qE '<!-- template: clawstodian/' AGENTS.md 2>/dev/null && echo "OK  agents marker" || echo "FAIL agents marker"
grep -qE '<!-- template: clawstodian/' HEARTBEAT.md 2>/dev/null && echo "OK  heartbeat marker" || echo "FAIL heartbeat marker"

# Reference templates present at workspace root
[ -f AGENTS.md ] && echo "OK  AGENTS.md present" || echo "FAIL AGENTS.md missing"
[ -f HEARTBEAT.md ] && echo "OK  HEARTBEAT.md present" || echo "FAIL HEARTBEAT.md missing"

# Workspace symlinks resolve
readlink -e clawstodian/programs >/dev/null 2>&1 && echo "OK  programs symlink" || echo "FAIL programs symlink"
readlink -e clawstodian/routines >/dev/null 2>&1 && echo "OK  routines symlink" || echo "FAIL routines symlink"
readlink -e clawstodian/scripts  >/dev/null 2>&1 && echo "OK  scripts symlink"  || echo "FAIL scripts symlink"

# Program specs reachable (four domain authorities)
for name in daily-notes para workspace repo; do
  [ -f "clawstodian/programs/${name}.md" ] && echo "OK  program ${name}" || echo "FAIL program ${name}"
done

# Routine specs reachable (seven scheduled dispatchers)
for name in sessions-capture daily-seal para-extract para-align workspace-clean git-clean health-check; do
  [ -f "clawstodian/routines/${name}.md" ] && echo "OK  routine ${name}" || echo "FAIL routine ${name}"
done

# Helper scripts reachable and executable
[ -x "clawstodian/scripts/scan-sessions.py" ] && echo "OK  scan-sessions.py executable" || echo "FAIL scan-sessions.py (missing or not executable)"

# Reference templates installed
for f in memory/para-structure.md memory/daily-note-structure.md MEMORY.md memory/crons.md memory/session-ledger.md; do
  [ -f "$f" ] && echo "OK  template ${f}" || echo "MISSING template ${f}"
done

# Cron jobs registered
for name in sessions-capture workspace-clean git-clean para-align daily-seal para-extract health-check; do
  openclaw cron list --all 2>/dev/null | grep -q " ${name} " && echo "OK  cron ${name}" || echo "FAIL cron ${name}"
done

# Heartbeat trace file present (or prepare it for first tick)
[ -f memory/heartbeat-trace.md ] && echo "OK  heartbeat-trace" || { touch memory/heartbeat-trace.md && echo "OK  heartbeat-trace (created)"; }
```

Any `FAIL` should be investigated before relying on the install.

## Session visibility config

The `sessions-capture` routine runs in an isolated cron session. By default, isolated sessions can only see their own spawned children - which means zero session transcripts to capture from. clawstodian requires `tools.sessions.visibility: "all"` in `~/.openclaw/openclaw.json`:

```bash
openclaw config show 2>/dev/null | grep -A1 '"sessions"' | grep -q '"visibility": *"all"' && echo "OK  sessions visibility = all" || echo "FAIL sessions visibility != all (capture will be silent)"
```

If this check fails, the capture routines will silently return zero captured content every tick. This is the single most load-bearing config in the daily-notes program.

## Heartbeat config sanity check

The heartbeat lives in `~/.openclaw/openclaw.json` (or `config.toml`), not in the workspace. Read it and confirm:

- `agents.defaults.heartbeat.every` is set (recommended: `"2h"`).
- `agents.defaults.heartbeat.target` is set to a channel plugin (`discord`, `slack`, `telegram`, etc.) and `agents.defaults.heartbeat.to` is set to the channel-specific recipient (e.g. `"channel:<id>"`). Avoid `target: "last"` - the notifications channel should be stable.
- `agents.defaults.heartbeat.activeHours` has `start`, `end`, `timezone` - matches the operator's preferred window.
- `channels.defaults.heartbeat.showAlerts` is `true`.
- `agents.defaults.heartbeat.session`, `isolatedSession`, and `lightContext` are either omitted (defaults) or set to: no `session` override, `isolatedSession: false`, `lightContext: false`. These defaults mean heartbeat runs in the agent's main session with full workspace bootstrap.

A config that passes every other check but has an unregistered `target` plugin, a malformed `to` recipient, or `showAlerts: false` will produce a silent heartbeat. That is the silent-heartbeat failure mode the package is designed to prevent; catch it here.

**Not checked here:** `session.maintenance`, `agents.defaults.contextPruning`, `session.dmScope`, `session.reset`. These are host-wide policy choices from the operator's sessions baseline; clawstodian does not prescribe them.

`docs/heartbeat-config.md` has the full reference.

## Burst-worker enable state

Burst workers (`sessions-capture`, `daily-seal`, `para-extract`) are expected to be **disabled at install time**. The heartbeat enables them on demand when a queue appears.

```bash
openclaw cron list --all | grep -E " (sessions-capture|daily-seal|para-extract) "
```

All three should show as disabled right after install. On a workspace with existing session history, `sessions-capture` will be enabled by the heartbeat's first tick and stay enabled until the ledger catches up; that is expected, not a failure. If any burst is enabled with an empty queue, the heartbeat's first tick will disable it automatically (safe but noisy).

## Session ledger sanity check

```bash
[ -f memory/session-ledger.md ] && echo "OK  session-ledger present" || echo "FAIL session-ledger missing"
grep -qE 'clawstodian/session-ledger' memory/session-ledger.md 2>/dev/null && echo "OK  session-ledger marker present" || echo "WARN session-ledger marker absent (OK if operator dropped markers)"

# Compare sessions_list count vs ledger entry count - only informational, not a pass/fail.
ledger_count=$(grep -c '^## ' memory/session-ledger.md 2>/dev/null || echo 0)
sessions_count=$(openclaw sessions list --json 2>/dev/null | jq 'length' 2>/dev/null || echo "?")
echo "INFO ledger has $ledger_count entries; sessions_list reports $sessions_count rows"
```

If `sessions_count > ledger_count` by a meaningful margin, the heartbeat should enable `sessions-capture` on its next tick. If `ledger_count > sessions_count`, some session transcripts have been pruned from disk; that's usually fine (ledger entries persist beyond their transcripts).

## Recent heartbeat evidence (optional, after first tick)

After the first real heartbeat tick fires:

```bash
tail -n 5 memory/heartbeat-trace.md
```

Each line is a tick record in the shape:

```
YYYY-MM-DDTHH:MM:SSZ | fired: <task names> | toggled: <cron changes> | notable: <one-line>
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
