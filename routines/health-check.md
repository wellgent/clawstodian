# health-check (routine)

Daily self-check on the clawstodian machinery: heartbeat config, session visibility, cron registrations, stalled routines, long-running bursts, workspace symlinks, and template markers. Detection only; findings surface for operator decision.

## Program

`clawstodian/programs/workspace.md` - conventions, authority, approval gates, and escalation.

This routine is cross-cutting: it observes clawstodian's own install-time contract and runtime state (heartbeat config, cron entries, symlinks, template markers) rather than a single domain's content. It touches `.openclaw/` and `openclaw cron list` state read-only, which is otherwise out of scope for the workspace program.

## Target

Clawstodian's install-time contract and runtime state, across four surfaces:

- **Gateway config** - `~/.openclaw/openclaw.json` (heartbeat stance + session visibility).
- **Cron registrations** - `openclaw cron list --all` output.
- **Workspace install artifacts** - `clawstodian/programs`, `clawstodian/routines`, and `clawstodian/scripts` symlinks; `clawstodian/scripts/scan-sessions.py` executable; template markers on installed reference docs.
- **Package freshness** - the clawstodian clone resolved via the workspace's `clawstodian/scripts` symlink: local-clone-vs-upstream drift (from `git fetch`), workspace-vs-clone template marker drift, CHANGELOG top version vs installed version.

## Steps

1. **Check heartbeat config.** Load `~/.openclaw/openclaw.json`. For each of `every`, `target`, `to`, `activeHours`, and `showAlerts` under `agents.defaults.heartbeat`, record the observed value. Recommended stance: `every: "2h"`, `target` set to a channel plugin (`discord` / `slack` / `telegram` / ...), `to` set to `"channel:<id>"`, `activeHours` set with `start` / `end` / `timezone`, `showAlerts: true`. Deviations are flagged, not enforced.

2. **Check session visibility.** Confirm `tools.sessions.visibility: "all"` in the same config file. Pass/fail, not a recommendation - anything else silently captures zero content for `sessions-capture`, which is the single most load-bearing config for the daily-notes pipeline.

3. **Check cron registrations.** Run `openclaw cron list --all`. Compare against the seven expected clawstodian routines: `sessions-capture`, `daily-seal`, `para-extract`, `para-align`, `workspace-clean`, `git-clean`, `health-check`. Note any missing, unexpected (stray clawstodian-adjacent name), or duplicate entry.

4. **Check stalled routines.** For each scheduled routine (`para-align` 168h, `workspace-clean` 168h, `git-clean` 12h, `health-check` 24h) and any currently-enabled burst: compare the timestamp on the newest `memory/runs/<routine>/*.md` file against the routine's expected interval. Flag any routine whose newest report is older than 2x its interval.

5. **Check long-running bursts.** Read `openclaw cron list --all` for each burst's enabled flag and (if enabled) the last state-transition timestamp (or infer from the oldest report in the current enablement window). Flag any burst exceeding its expected drain window: `sessions-capture` > 12h, `daily-seal` > 24h, `para-extract` > 24h with a non-shrinking queue.

6. **Verify workspace symlinks.** `readlink -e clawstodian/programs`, `readlink -e clawstodian/routines`, and `readlink -e clawstodian/scripts` each resolve to a package directory. Record the resolved paths. Additionally confirm `clawstodian/scripts/scan-sessions.py` is present and executable.

7. **Check template markers.** Grep each installed reference doc for its expected `<!-- template: clawstodian/... -->` line: workspace `AGENTS.md`, workspace `HEARTBEAT.md`, `memory/para-structure.md`, `memory/daily-note-structure.md`, `MEMORY.md`, `memory/crons.md`, `memory/session-ledger.md`. Marker presence only; content drift against the package is covered by step 8.

8. **Check package freshness.** Resolve the clawstodian clone root from the symlink: `REPO=$(dirname "$(readlink -e clawstodian/scripts)")`. Then three sub-checks:

   - **Local clone vs upstream.** `timeout 15 git -C "$REPO" fetch --quiet` (15s hard cap; tolerate failures silently - network / auth issues are not anomalies). Compute `git -C "$REPO" rev-list --count HEAD..@{u}` for the number of upstream commits not present locally. Non-zero → surface "local clone behind upstream by <N> commits; run `git -C <REPO> pull`".
   - **Workspace markers vs package markers.** For each installed template listed in step 7, compare the workspace file's marker date against the package file's marker date (e.g. `$REPO/templates/HEARTBEAT.md` line 1). Any workspace marker strictly older than the package marker → surface "template <name> is stale (<workspace-date> → <package-date>); re-run `~/clawstodian/INSTALL.md`".
   - **CHANGELOG top entry.** Read the first `## X.Y.Z - YYYY-MM-DD` line in `$REPO/CHANGELOG.md` - that is the current package version. Record it in the report for operator context. First non-empty paragraph under that header is the one-paragraph summary of what changed; surface it alongside any stale-template finding.

   Detection only. Do NOT `git pull`, do NOT re-run INSTALL, do NOT touch the workspace templates. The operator decides when to apply updates via `INSTALL.md`'s existing diff-and-propose flow.

9. **Aggregate.** Sum findings into the run report. No auto-repair - detection is the entire action.

## Exec safety

- Run commands by exact path. No `eval`, `bash -c "..."`, or other indirection that hides the real command from the gateway's exec safety layer.
- For multi-line script logic, write the script to `/tmp/clawstodian-health-check-<context>.py` (or `.sh`) and invoke it by path. Do not inline code via heredoc to an interpreter (`python3 <<EOF ... EOF`); the safety layer blocks that as obfuscation.
- `jq` and `python3 -c '<short expression>'` one-liners are fine when they fit on one line and the intent is obvious.

## Worker discipline

- Detection only. Never edit configs, restart services, repair symlinks, toggle crons, or touch template markers.
- Single pass per firing; no internal loops.
- Anomalies surface via the run report. Resolution is the operator's (and the heartbeat `reflect` task's aggregation) territory.
- Do not commit. This routine produces no content changes to stage.
- No self-disable; this cron is scheduled, not queue-driven.

## Run report

Two artifacts every firing: a full report on disk following the shared run-report shape, and a multi-line scannable summary posted to the notifications channel.

### File on disk

Write to `memory/runs/health-check/<YYYY-MM-DD>T<HH-MM-SS>Z.md`.

```markdown
# health-check run report

- timestamp: 2026-04-19T03:00:00Z
- context: 2026-04-19 daily
- outcome: ok

## What happened

### Heartbeat config

- every: 2h (ok)
- target: discord (ok)
- to: channel:XXXXX (ok)
- activeHours: 08:00-22:00 UTC (ok)
- showAlerts: true (ok)

### Session visibility

- tools.sessions.visibility: all (ok)

### Cron registrations

- expected: 7 (sessions-capture, daily-seal, para-extract, para-align, workspace-clean, git-clean, health-check)
- present: 7
- missing: (none)
- unexpected: (none)

### Stalled routines

- (none)

### Long-running bursts

- (none)

### Workspace symlinks

- clawstodian/programs -> /home/operator/clawstodian/programs (ok)
- clawstodian/routines -> /home/operator/clawstodian/routines (ok)

### Template markers

- AGENTS.md: clawstodian/agents (ok)
- HEARTBEAT.md: clawstodian/heartbeat (ok)
- memory/para-structure.md: clawstodian/para-structure (ok)
- memory/daily-note-structure.md: clawstodian/daily-note-structure (ok)
- MEMORY.md: clawstodian/memory (ok)
- memory/crons.md: clawstodian/crons (ok)
- memory/session-ledger.md: clawstodian/session-ledger (ok)

### Package freshness

- clone: /home/operator/clawstodian
- installed version: 0.4.1 (from CHANGELOG.md top entry)
- upstream: HEAD == @{u} (up to date)
- stale templates: (none)

## Commits

- (none - health-check does not commit)

## Surfaced for operator

- (none)

## Channel summary

health-check · 2026-04-19 · ok
Config: ok · visibility: all
Crons: 7/7 registered · 0 stalled · 0 long-running
Symlinks: ok · markers: 7/7
Package: 0.4.1 (up to date)
Report: memory/runs/health-check/2026-04-19T03-00-00Z.md
```

Keep the full skeleton on the file-on-disk even on a clean firing; a reader scanning it always knows which checks ran. Anomalies fill in the relevant subsection.

### Channel summary

Multi-line. One concern per line, matching the shape routines share:

```
health-check · <date> · <outcome>
Config: <ok|drift:<N>> · visibility: <all|tree|other>
Crons: <R>/7 registered · <S> stalled · <L> long-running
Symlinks: <ok|<B> broken> · markers: <M>/7
Package: <version> (<up to date | N behind upstream | <K> stale templates>)
Report: memory/runs/health-check/<ts>.md
```

- `outcome` is `ok | anomaly | failed`. `ok` means every check passed. `anomaly` means one or more checks flagged a deviation; the run-report file details each. `failed` means the routine itself could not complete (e.g. `~/.openclaw/openclaw.json` unreadable).
- On a healthy firing every middle line reads `ok` / `all` / `0` / `N/N` / `up to date`; counts do the work on an anomaly firing. The operator drills into the run-report file for per-check detail.
- Every firing speaks. A healthy firing still produces a full channel post plus the run-report file - evidence that the observability layer itself is alive.
