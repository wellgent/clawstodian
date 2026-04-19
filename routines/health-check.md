# health-check (routine)

Daily self-check on the clawstodian machinery: heartbeat config, session visibility, cron registrations, stalled routines, long-running bursts, workspace symlinks, and template markers. Detection only; findings surface for operator decision.

## Program

`clawstodian/programs/workspace.md` - conventions, authority, approval gates, and escalation.

This routine is cross-cutting: it observes clawstodian's own install-time contract and runtime state (heartbeat config, cron entries, symlinks, template markers) rather than a single domain's content. It touches `.openclaw/` and `openclaw cron list` state read-only, which is otherwise out of scope for the workspace program.

## Target

Clawstodian's install-time contract and runtime state, across three surfaces:

- **Gateway config** - `~/.openclaw/openclaw.json` (heartbeat stance + session visibility).
- **Cron registrations** - `openclaw cron list --all` output.
- **Install currency** - workspace symlinks (`clawstodian/programs`, `routines`, `scripts`), `scan-sessions.py` executable, per-template marker presence + freshness against the package, local clone vs upstream, CHANGELOG top version.

## Steps

1. **Check heartbeat config.** Load `~/.openclaw/openclaw.json`. For each of `every`, `target`, `to`, `activeHours`, and `showAlerts` under `agents.defaults.heartbeat`, record the observed value. Recommended stance: `every: "2h"`, `target` set to a channel plugin (`discord` / `slack` / `telegram` / ...), `to` set to `"channel:<id>"`, `activeHours` set with `start` / `end` / `timezone`, `showAlerts: true`. Deviations are flagged, not enforced.

2. **Check session visibility.** Confirm `tools.sessions.visibility: "all"` in the same config file. Pass/fail, not a recommendation - anything else silently captures zero content for `sessions-capture`, which is the single most load-bearing config for the daily-notes pipeline.

3. **Check cron registrations.** Run `openclaw cron list --all`. Compare against the seven expected clawstodian routines: `sessions-capture`, `daily-seal`, `para-extract`, `para-align`, `workspace-clean`, `git-clean`, `health-check`. Note any missing, unexpected (stray clawstodian-adjacent name), or duplicate entry.

4. **Check stalled routines.** For each scheduled routine (`para-align` 168h, `workspace-clean` 168h, `git-clean` 12h, `health-check` 24h) and any currently-enabled burst: compare the timestamp on the newest `memory/runs/<routine>/*.md` file against the routine's expected interval. Flag any routine whose newest report is older than 2x its interval.

5. **Check long-running bursts.** Read `openclaw cron list --all` for each burst's enabled flag and (if enabled) the last state-transition timestamp (or infer from the oldest report in the current enablement window). Flag any burst exceeding its expected drain window: `sessions-capture` > 12h, `daily-seal` > 24h, `para-extract` > 24h with a non-shrinking queue.

6. **Verify workspace symlinks.** `readlink -e clawstodian/programs`, `readlink -e clawstodian/routines`, and `readlink -e clawstodian/scripts` each resolve to a package directory. Record the resolved paths. Additionally confirm `clawstodian/scripts/scan-sessions.py` is present and executable.

7. **Check install currency.** Compare the workspace install against the package clone it's pinned to. Resolve the clone root first: `REPO=$(dirname "$(readlink -e clawstodian/scripts)")`. Then:

   - **Per-template marker.** For each installed reference doc (workspace `AGENTS.md`, `HEARTBEAT.md`, `memory/para-structure.md`, `memory/daily-note-structure.md`, `MEMORY.md`, `memory/crons.md`, `memory/session-ledger.md`): read the `<!-- template: clawstodian/<name> YYYY-MM-DD -->` marker line. Missing → surface "marker absent for <path>". Present but strictly older than the matching package file's marker (`$REPO/templates/<name>.md` line 1) → surface "template <name> is stale (<workspace-date> → <package-date>); re-run `~/clawstodian/INSTALL.md`".
   - **Local clone vs upstream.** `timeout 15 git -C "$REPO" fetch --quiet` (15s hard cap; tolerate failures silently - network / auth issues are not anomalies). Compute `git -C "$REPO" rev-list --count HEAD..@{u}` for the number of upstream commits not present locally. Non-zero → surface "local clone behind upstream by <N> commits; run `git -C <REPO> pull`".
   - **CHANGELOG top entry.** Read the first `## X.Y.Z - YYYY-MM-DD` line in `$REPO/CHANGELOG.md` - that is the current package version. Record it in the report for operator context. First non-empty paragraph under that header is the one-paragraph release summary; surface it alongside any stale-template finding.

   Detection only. Do NOT `git pull`, do NOT re-run INSTALL, do NOT touch the workspace templates. The operator decides when to apply updates via `INSTALL.md`'s existing diff-and-propose flow.

8. **Observe ledger and session-state.** Run the authoritative queue source for a daily pulse on the daily-notes pipeline:

   ```bash
   clawstodian/scripts/scan-sessions.py > /tmp/clawstodian-health-scan.json
   ```

   Read `.counts` from the output. Also count ledger entries directly: `grep -c '^## ' memory/session-ledger.md`. Record in the run report: `ledger entries: <N>`, `sessions_list interactive: <counts.interactive>`, `queue: <len(queue)>`, `missing_transcripts: <counts.missing_transcript>`, full skipped breakdown.

   Surface only durable anomalies (thresholds are rules of thumb; refine when patterns emerge):
   - **Queue > 0 on a daily-scheduled firing** where `sessions-capture` cron has been enabled for >24h without draining. Signals a stuck burst (sessions-capture firing but not making progress).
   - **Ledger entries > 2x `counts.interactive`** suggests orphan accumulation beyond what the natural attrition of transcript pruning explains. Informational; not actionable until operator decides to prune.
   - **`counts.missing_transcript` growing week over week.** Registry drift (sessions in `sessions_list` whose jsonl files are gone). Usually benign when small, worth surfacing when consistent.

   All observational. No migration triggers, no narrow one-release checks. This block stays useful as long as the daily-notes pipeline exists.

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

### Install currency

- clone: /home/operator/clawstodian
- package version: 0.4.1 (from CHANGELOG.md top entry)
- upstream: HEAD == @{u} (up to date)
- template markers:
  - AGENTS.md: clawstodian/agents 2026-04-19 (ok)
  - HEARTBEAT.md: clawstodian/heartbeat 2026-04-19 (ok)
  - memory/para-structure.md: clawstodian/para-structure 2026-04-18 (ok)
  - memory/daily-note-structure.md: clawstodian/daily-note-structure 2026-04-19 (ok)
  - MEMORY.md: clawstodian/memory 2026-04-18 (ok)
  - memory/crons.md: clawstodian/crons 2026-04-19 (ok)
  - memory/session-ledger.md: clawstodian/session-ledger 2026-04-19 (ok)
- stale templates: (none)

### Ledger and session state

- ledger entries: 59
- sessions_list interactive: 14 · queue: 0 · missing_transcripts: 2
- skipped: cron=36 · hook=0 · subagent=5 · dreaming=294 · empty=12
- anomalies: (none - ledger size consistent with interactive count; queue drained; missing_transcripts stable)

## Commits

- (none - health-check does not commit)

## Surfaced for operator

- (none)

## Channel summary

health-check · 2026-04-19 · ok
Config: ok · visibility: all
Crons: 7/7 registered · 0 stalled · 0 long-running
Symlinks: ok
Install: 0.4.1 · up to date · markers 7/7 fresh
Ledger: 59 entries · interactive=14 · queue=0 · missing_transcripts=2
Report: memory/runs/health-check/2026-04-19T03-00-00Z.md
```

Keep the full skeleton on the file-on-disk even on a clean firing; a reader scanning it always knows which checks ran. Anomalies fill in the relevant subsection.

### Channel summary

Multi-line. One concern per line, matching the shape routines share:

```
health-check · <date> · <outcome>
Config: <ok|drift:<N>> · visibility: <all|tree|other>
Crons: <R>/7 registered · <S> stalled · <L> long-running
Symlinks: <ok|<B> broken>
Install: <version> · <up to date | N behind upstream> · markers <F>/7 fresh
Ledger: <N> entries · interactive=<I> · queue=<Q> · missing_transcripts=<M>
Report: memory/runs/health-check/<ts>.md
```

- `outcome` is `ok | anomaly | failed`. `ok` means every check passed. `anomaly` means one or more checks flagged a deviation; the run-report file details each. `failed` means the routine itself could not complete (e.g. `~/.openclaw/openclaw.json` unreadable).
- On a healthy firing every middle line reads `ok` / `all` / `0` / `N/N` / `up to date` / `7/7 fresh`; counts do the work on an anomaly firing. The operator drills into the run-report file for per-check detail.
- Every firing speaks. A healthy firing still produces a full channel post plus the run-report file - evidence that the observability layer itself is alive.
