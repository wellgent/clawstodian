# clawstodian architecture

## Goal

Deliver every job the `ops-daily` / `ops-para` / `ops-clean` packages did, through native OpenClaw primitives, with no package-owned state and no worker choreography.

The design target is a system an operator can monitor, audit, troubleshoot, and trust. Intelligence lives in markdown the agent reads; the harness is thin; every meaningful action is observable by default.

## Design principles

### 1. Native primitives over invented machinery

Use what OpenClaw ships:
- `AGENTS.md` for standing authority (loaded first in context).
- `HEARTBEAT.md` for the orchestrator loop.
- Heartbeat for the orchestrator's cadence.
- Cron as the execution substrate for every routine.
- Session transcripts for auditability.
- Session tools (`sessions_list`, `sessions_history`) and raw disk JSONL for transcript access.

Avoid building a parallel orchestration layer.

### 2. Cron is the execution substrate; heartbeat is the orchestrator

Every routine runs as its own cron job with `--session isolated --light-context`. Cron persists jobs to disk, supports wall-clock-absolute schedules, and emits one observable delivery path per job; these qualities make the execution layer resilient and self-observing by default.

The heartbeat does not execute routines. Each tick it:

1. Reads workspace state fresh (daily notes, PARA, git status, cron last-run times).
2. Toggles heartbeat-managed burst workers (`seal-past-days`, `para-extract`) based on their queue state.
3. May `--wake now` `para-align` if mid-week structural drift was reported.
4. Spot-checks health (config drift, missing crons, broken symlinks).
5. Appends a trace line to `memory/heartbeat-trace.md`.
6. Posts a one-line executive summary to the logs channel - never silent.

This inverts the v0.3 pure-prose dispatcher (which silently dropped ticks when any of seven heartbeat gates short-circuited) toward the `ops-daily` debuggability pattern: cron-per-job with per-job notifications.

### 3. Three observability layers

A healthy install emits three streams, each serving a different reader:

- **Per-routine announcement** (detail on demand). Each cron routine posts a single-line reply to the logs channel on every run that changes something. Quiet runs reply `NO_REPLY` and stay silent.
- **Heartbeat executive summary** (ambient awareness). Every tick posts one line summarizing queues, recent routine activity, and health. Never silent - a tick with nothing to do still posts.
- **Tick trace file** (forensic record). `memory/heartbeat-trace.md` is an append-only log an operator can `grep` or `tail` to prove heartbeat fired and see what it observed.

Silence in any of the three is itself a signal. A dead heartbeat is not ambiguous.

### 4. The workspace is the ledger

No package-owned state files. Git, daily notes, PARA entities, `MEMORY.md`, session transcripts, and `memory/heartbeat-trace.md` are the only state. Every routine and every heartbeat tick derives what it needs from those artifacts, acts, writes observations back, and forgets.

This is why `isolatedSession: true` and `lightContext: true` are correct for both heartbeat ticks and routine runs. Cross-tick memory lives in files, not session history. The workspace bootstrap (`AGENTS.md`, `MEMORY.md`) caches across ticks within OpenClaw's prompt-cache window; routine specs are read fresh on every run, so spec updates take effect without re-registering crons.

Note the interaction: `lightContext: true` skips the full workspace bootstrap except `HEARTBEAT.md`. Routines that need `MEMORY.md`, `AGENTS.md`, or PARA reference docs must explicitly read them. Specs in this package do so where needed.

### 5. Co-create, do not guess

The agent has judgment but not taste. When placement, filing, or risk is obvious, it acts. When ambiguous, it surfaces the ambiguity in the routine's reply and leaves the state untouched.

Per-routine announcements mean the operator sees ambiguities in the channel the same way they see completions. There is no "batch tick summary" to hide inside; every routine speaks for itself.

### 6. Small reversible actions over broad audits

The maintainer prefers one concrete small change over a theoretical sweep. It surfaces emerging projects or misfiled efforts but does not silently promote them. Escalates before anything destructive, risky, or ambiguous.

## Primitive mapping

```
standing authority       AGENTS.md             (charter + six routines)
orchestrator loop        HEARTBEAT.md          (reads state, toggles bursts, posts summary)
orchestrator cadence     heartbeat             (2h default, active hours, isolated session)
routine execution        cron                  (every routine is its own cron job)
audit trail              logs channel + session transcripts + git + heartbeat-trace.md
workspace memory         memory/, projects/, areas/, resources/, archives/
```

There is no "standing orders" primitive in the OpenClaw codebase; the term in OpenClaw's docs refers to rules written into `AGENTS.md`. clawstodian uses the standing-orders anatomy (authority / trigger / approval gate / escalation / execution steps / what NOT to do) to structure each routine, but the mechanism remains the AGENTS.md file loaded at session bootstrap and the cron job that dispatches the routine with a `Read clawstodian/routines/<name>.md and execute.` message.

## The six routines

Each routine has a single-page spec in `routines/`. `AGENTS-SECTION.md` catalogs them; individual specs are read on demand when a cron fires.

| Routine | Class | Schedule | Replaces |
| - | - | - | - |
| `daily-note` | always-on cron | every 30m | `daily-notes-tend` + `durable-insight` inline |
| `workspace-tidy` | always-on cron | every 2h | `workspace-tidiness` (expanded: active filing) |
| `git-hygiene` | always-on cron | every 30m | `git-hygiene` (unchanged in function) |
| `para-align` | fixed cron | Sunday 06:00 UTC | `weekly-para-align` (expanded: cross-refs, naming, MEMORY.md) |
| `seal-past-days` | heartbeat-toggled burst | every 30m while enabled | `close-of-day` |
| `para-extract` | heartbeat-toggled burst | every 30m while enabled | `para-backfill` + `para-tend` + `durable-insight` PARA filing |

Two execution classes:

- **Always-on cron** - enabled at install time; fires on its schedule; quiet runs reply `NO_REPLY`.
- **Heartbeat-toggled burst** - starts disabled; heartbeat enables when a queue exists and disables when empty.

## Observability and troubleshooting

A working clawstodian install is debuggable from a small set of surfaces:

1. **Logs channel** - per-routine announcements and heartbeat executive summaries arrive here.
2. **`memory/heartbeat-trace.md`** - append-only tick log, greppable by date.
3. **`openclaw cron list --all`** - which routines are registered, which are enabled, last-run timestamps.
4. **`AGENTS.md`** - routine catalog and authority.
5. **`HEARTBEAT.md`** - orchestrator loop.
6. **`memory/crons.md`** - operator-readable cron dashboard.

If an operator needs to look at more than that to explain routine behavior, the design has drifted.

## Non-goals

- Full transcript-to-memory coverage. `daily-note` does its best from `sessions_*` and git; it does not exhaustively reconstruct everything.
- Automatic PARA rewrites. `para-extract` creates and updates obvious placements; `para-align` applies trivial structural fixes; neither reorganizes existing entities without operator direction.
- Hidden state. Any persistent fact the package acts on is a file the operator can read.
- Multi-worker pipelines. Each routine is one cron, one session, one single-line reply.
- Auto-archive lifecycle. When inactive projects move from live PARA into `archives/` stays user-managed judgment.
- Custom hooks in the default path. If a future feature needs hooks, it will be documented as opt-in, not baseline.

## Open questions

- Periodic workspace-audit routine: deferred. The install smoke test covers install-time correctness; an audit routine that verifies ongoing delivery is a separate iteration.
- Fixed cron with heartbeat-wake for `para-align` is v0.4's pragmatic solution; a fully declarative "trigger when drift report matches X" would need a queue primitive the package does not have yet.
- `MEMORY.md` + `lightContext: true` interaction: isolated sessions do not auto-load `MEMORY.md`; routines that need it read it explicitly. Worth a test before adding a routine that depends on it.
