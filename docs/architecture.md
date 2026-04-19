# clawstodian architecture

## Goal

Keep a workspace in good shape via native OpenClaw primitives, with no package-owned state and no worker choreography.

The design target is a system an operator can monitor, audit, troubleshoot, and trust. Intelligence lives in markdown the agent reads; the harness is thin; every meaningful action is observable by default.

## Design principles

### 1. Programs are authorities; routines are invocations

The package splits behavior from scheduling at the file level.

- A **program** (`programs/<name>.md`) is a durable statement of how the workspace operates in one domain: conventions, authority, approval gates, escalation rules, and the full set of behaviors the agent can perform. Programs are read at session bootstrap via `AGENTS.md` so every agent in the workspace knows how the domain is governed. They change only when the domain's convention changes.
- A **routine** (`routines/<name>.md`) is a thin scheduled invocation: a reference to a program plus the behavior to invoke, a target, a run-report format, worker discipline, and a cron install command. Routines are read only inside cron dispatch. Cadences and report formats change freely without touching programs.

Programs answer *what is true about this domain, always?* Routines answer *what do we run, when, and how do we report it?* Multiple routines can reference the same program, which is the expected shape (for example, both `sessions-capture` and `daily-seal` routines reference behaviors from the `daily-notes` program).

### 2. Native primitives over invented machinery

Use what OpenClaw ships:
- `AGENTS.md` for standing authority (loaded first in context) - carries the programs catalog.
- `HEARTBEAT.md` for the orchestrator loop.
- Heartbeat for the orchestrator's cadence.
- Cron as the execution substrate for every routine.
- Session transcripts for auditability.
- Session tools (`sessions_list`, `sessions_history`) and raw disk JSONL for transcript access.

Avoid building a parallel orchestration layer.

### 3. Cron is the execution substrate; heartbeat is the collaborative maintainer

Every routine runs as its own cron job with `--session isolated --light-context`. Cron persists jobs to disk, supports wall-clock-absolute schedules, and emits one observable delivery path per job; these qualities make the execution layer resilient and self-observing by default.

The heartbeat does not execute programs or routines. It is the collaborative maintenance thread between the operator and the agent, bounded to a narrow set of jobs only the orchestrator can do. Each tick it:

1. Tends the three burst workers (`sessions-capture`, `daily-seal`, `para-extract`): detects each one's queue from its routine spec, toggles its cron to match.
2. Sets `capture_status: done` on past-active daily notes when the ledger conditions hold - the gate that lets `daily-seal` fire.
3. Reads new run reports from routines whose tending task is firing this tick and flags anomalies.
4. Appends a trace line to `memory/heartbeat-trace.md`.
5. Posts a brief combined summary to the notifications channel - never silent.
6. Once per day, reflects: scans new run reports across all routines (including `health-check`), aggregates operator-surfaced items, writes a narrative directly to the operator in the DM.

Machinery sanity checks (heartbeat-config drift, session visibility, cron registration, stalled routines, long-running bursts, workspace symlinks, template markers) are not done inline; they live in the `health-check` routine which fires daily and writes its own run report. The heartbeat observes those findings via the `reflect` task.

The heartbeat runs in the agent's main session (the operator's DM with the agent), so the maintenance thread is continuous with whatever the operator and the agent have been discussing. The notifications channel is a separate, read-mostly observability surface: heartbeat summaries and per-routine announcements all land there. Collaboration happens in the DM; observation happens in the channel.

Mixed cadence is managed through a `tasks:` YAML block in `templates/HEARTBEAT.md`: `tend-sessions-capture` fires every tick (2h interval matches the gateway `every: 2h`); `tend-daily-seal`, `tend-para-extract`, and `reflect` each fire once per day. Only due tasks fire on a given tick, keeping cost bounded. When multiple tasks fire in a single tick (e.g. the daily tick), they produce ONE combined channel post.

See `docs/heartbeat-config.md` for the rationale and recommended gateway config, and `docs/crons-config.md` for the cron-job flag stack.

### 4. Four continuity layers

A healthy install carries continuity on four layers, each serving a different need:

- **Per-routine announcement** (detail on demand). Each cron routine posts a multi-line scannable summary to the notifications channel on every firing and writes a detailed run-report file to `memory/runs/<routine>/<timestamp>.md`. Even a quiet firing ("nothing to do") produces both artifacts, so silence in the channel is never ambiguous - it means the cron did not fire.
- **Heartbeat notifications posts** (running observability). Every tick posts at least a status line; longer cadences add reflections and reviews. This channel is read-mostly - it's the pane of glass on workspace maintenance activity.
- **Main session history** (collaborative memory). The heartbeat runs in the operator's main DM session with the agent, so past tick outputs, operator replies, and in-flight decisions all accumulate as conversation history. Host-wide session maintenance (compaction) bounds growth.
- **Tick trace file** (forensic record). `memory/heartbeat-trace.md` is an append-only log independent of session state. Greppable and permanent. Survives compaction, session deletion, and anything else that might trim session history.

Silence in any of the four is itself a signal. A dead heartbeat is not ambiguous.

### 5. The workspace is the ledger

No package-owned state files. Git, daily notes, PARA entities, `MEMORY.md`, session transcripts, `memory/session-ledger.md`, `memory/heartbeat-trace.md`, and per-routine run reports under `memory/runs/<routine>/` are the only state. Every routine and every heartbeat tick derives what it needs from those artifacts, acts, writes observations back, and forgets.

The `daily-notes` program is the most state-dependent: it needs to know which interactive sessions it has already captured, and how far into each transcript. That state lives in `memory/session-ledger.md` - one markdown section per interactive session, cursor fields advanced in place via narrow `Edit` calls. Cursors advance only after the affected daily-note writes succeed; a partial failure leaves the cursor at the old position so the next tick retries from there.

The ledger contains interactive sessions only. Skipped classifications (cron-dispatched, hook-dispatched, sub-agent, dreaming-routine, delivery-only) are not stored - they are re-derived on every scan by `clawstodian/scripts/scan-sessions.py`, which is the single authoritative queue source shared between the heartbeat's burst-enable decision and the `sessions-capture` routine's target selection.

This is why `isolatedSession: true` and `lightContext: true` are correct for routine runs. Cross-tick memory lives in files, not session history. The workspace bootstrap (`AGENTS.md`, `MEMORY.md`) caches across ticks within OpenClaw's prompt-cache window; program and routine specs are read fresh on every run, so spec updates take effect without re-registering crons.

Note the interaction: `lightContext: true` skips the full workspace bootstrap except `HEARTBEAT.md`. Routines that need `MEMORY.md`, `AGENTS.md`, or PARA reference docs must explicitly read them. Specs in this package do so where needed.

Note also the one OpenClaw config prerequisite: `tools.sessions.visibility: "all"`. Without it, isolated cron sessions cannot see sibling sessions' transcripts, so the `sessions-capture` routine silently captures zero content. This is the sharpest edge in the install and VERIFY explicitly checks it.

### 6. Co-create, do not guess

The agent has judgment but not taste. When placement, filing, or risk is obvious, it acts. When ambiguous, it surfaces: during a session, in chat to the user; under cron dispatch, in the routine's run report to the logs channel.

Per-routine announcements mean the operator sees ambiguities in the channel the same way they see completions. There is no "batch tick summary" to hide inside; every routine speaks for itself.

### 7. Small reversible actions over broad audits

The maintainer prefers one concrete small change over a theoretical sweep. It surfaces emerging projects or misfiled efforts but does not silently promote them. Escalates before anything destructive, risky, or ambiguous.

### 8. Queue derivation over queue storage

The daily-notes pipeline does not store its work queue. It stores cursors (in `memory/session-ledger.md`), and derives the queue on demand from `clawstodian/scripts/scan-sessions.py`. The script combines three inputs - live `sessions_list`, the ledger, and on-disk transcript line counts - and emits the interactive-session queue as JSON.

The script is the queue function; the ledger is one of its three inputs, not a drop-in replacement. Two independent consumers use the same function at their own cadence:

- **Heartbeat `tend-sessions-capture`** (every 2h) - invokes the script, reads `.queue` length, enables or disables the burst cron. Writes nothing.
- **`sessions-capture` burst** (every 30m while enabled) - invokes the script, processes items from the queue, advances cursors in the ledger.

Neither hands data to the other. Each runs the script fresh because:

- Time gap - up to 30 minutes between the orchestrator's decision and the burst firing. New sessions appear, existing ones gain activity. A frozen snapshot would be stale.
- No handoff channel - OpenClaw cron dispatches a fixed prompt; there is no way to pass a JSON payload from orchestrator to burst.
- Self-correcting - if orchestrator and reality disagree (race between enable and fire, or an in-session agent closed the gap), the burst re-scans and no-ops gracefully.

The script runs in milliseconds even against hundreds of sessions. Re-derivation is cheaper than any coordination mechanism.

This is the general pattern: **where state can be derived cheaply from workspace artifacts, derive it each time instead of caching it.** Caches introduce invalidation logic; derivation is stateless. The ledger stores only what cannot be derived (cursors into transcripts the agent has already read).

## Primitive mapping

```
standing authority           AGENTS.md + programs/     (charter + four domain authorities)
collaborative maintainer     HEARTBEAT.md              (reads state, toggles bursts, reflects, converses)
maintainer cadence           heartbeat                 (2h, main session, active hours, full bootstrap)
maintainer continuity        main session history      (conversation with the operator, host-wide compaction)
scheduled invocations        routines/ + cron          (seven routines; each a cron job in its own isolated session)
capture state                memory/session-ledger.md  (per-interactive-session cursor; skipped classes not stored)
classification + queue        clawstodian/scripts/scan-sessions.py  (re-derived from sessions_list + ledger)
run reports                  memory/runs/<routine>/    (per-firing detail files; pruned by workspace-clean after 30d)
audit trail                  notifications channel + session transcripts + git + heartbeat-trace.md
workspace memory             memory/, projects/, areas/, resources/, archives/
```

## Four programs, seven routines

Programs (authorities):

- **`daily-notes`** - canonical daily notes: `memory/YYYY-MM-DD.md` per day. Behaviors: Capture one session's new content; Seal a past-day note.
- **`para`** - PARA knowledge graph: `projects/` / `areas/` / `resources/` / `archives/`. Behaviors: Extract PARA from a sealed note; Align PARA structure.
- **`workspace`** - workspace tree outside PARA. Behavior: Walk and tidy.
- **`repo`** - git repository discipline. Behavior: Commit drift.

Routines (scheduled invocations):

- **`sessions-capture`** - daily-notes / Capture one session's new content - heartbeat-toggled burst, every 30m while enabled.
- **`daily-seal`** - daily-notes / Seal a past-day note - heartbeat-toggled burst, every 30m while enabled.
- **`para-extract`** - para / Extract PARA from a sealed note - heartbeat-toggled burst, every 30m while enabled.
- **`para-align`** - para / Align PARA structure - scheduled, Sunday 06:00 UTC.
- **`workspace-clean`** - workspace / Walk and tidy - scheduled, Sunday 07:00 UTC.
- **`git-clean`** - repo / Commit drift - scheduled, 01:00 and 11:00 UTC daily.
- **`health-check`** - workspace (cross-cutting) / observes the clawstodian machinery itself - scheduled, 03:00 UTC daily. Read-only; anomalies surface for operator decision via the heartbeat's daily `reflect`.

Two execution classes for routines:

- **Scheduled** - enabled at install time; fires on its wall-clock schedule; stays enabled; no self-disable. Every firing produces a run-report file and channel post (including quiet firings with `outcome: clean` or `no-op`).
- **Heartbeat-toggled burst** - starts disabled; heartbeat enables when a queue exists and disables when empty; routine self-disables when it drains the queue.

Three heartbeat-toggled bursts (`sessions-capture`, `daily-seal`, `para-extract`) form a pipeline: `sessions-capture` populates daily notes from session transcripts that the agents did not write up in-session; `daily-seal` closes past-day notes with `para_status: pending`; `para-extract` propagates those sealed notes into PARA entities. Each stage signals readiness via workspace state (ledger entries, frontmatter flags), not in-memory queues. The heartbeat reads those signals once per tick and flips the corresponding crons on or off.

Agents in live sessions remain the primary writers of daily notes per `AGENTS.md` memory-maintenance rules; `sessions-capture` is the backstop. Each firing invokes `clawstodian/scripts/scan-sessions.py`, pulls the interactive queue, and processes one session at a time end-to-end until the queue is empty or the firing budget is spent. On a disciplined workspace most transcript content is already in the daily note, and the per-date merge rule absorbs matches rather than duplicating.

## Observability and troubleshooting

A working clawstodian install is debuggable from a small set of surfaces:

1. **Logs channel** - per-routine run-report summaries and heartbeat executive summaries arrive here. Each summary points to the corresponding file on disk for drill-down.
2. **`memory/runs/<routine>/`** - per-firing detailed run reports. Files named `<YYYY-MM-DD>T<HH-MM-SS>Z.md`, sorted chronologically. Pruned by `workspace-clean` after 30 days.
3. **`memory/heartbeat-trace.md`** - append-only tick log, greppable by date.
4. **`openclaw cron list --all`** - which routines are registered, which are enabled, last-run timestamps.
5. **`AGENTS.md` (programs catalog)** - domain authorities.
5. **`HEARTBEAT.md`** - orchestrator loop.
6. **`memory/crons.md`** - operator-readable cron dashboard.

If an operator needs to look at more than that to explain routine behavior, the design has drifted.

## Non-goals

- Full transcript-to-memory coverage. The daily-notes program does its best from `sessions_*` and git; it does not exhaustively reconstruct everything.
- Automatic PARA rewrites. The para program creates and updates obvious placements in extract, applies trivial structural fixes in align; neither reorganizes existing entities without operator direction.
- Hidden state. Any persistent fact the package acts on is a file the operator can read.
- Multi-worker pipelines. Each routine is one cron, one session, one multi-line scannable report.
- Auto-archive lifecycle. When inactive projects move from live PARA into `archives/` stays user-managed judgment.
- Custom hooks in the default path. If a future feature needs hooks, it will be documented as opt-in, not baseline.

## Open questions

- Periodic install-time smoke test in `VERIFY.md` covers correctness at install. `health-check` covers ongoing machinery sanity (config drift, cron registration, stalled routines, symlinks, template markers). A richer audit routine that verifies ongoing delivery (queue drain rates, capture coverage) is deferred.
- Mid-week drift detected by `para-extract` waits for the next weekly `para-align` firing unless the operator decides to run `para-align` ahead of schedule. A fully declarative "trigger when drift report matches X" would need a queue primitive the package does not have yet.
- `MEMORY.md` + `lightContext: true` interaction: isolated cron sessions do not auto-load `MEMORY.md`; routines that need it read it explicitly. Worth a test before adding a routine that depends on it.
- Notifications channel is intentionally read-mostly. Replies in the channel route to the channel's auto-derived session (OpenClaw routing behavior), not to the main session where the heartbeat runs. The operator collaborates with the agent in the DM, reads the channel for observability.
