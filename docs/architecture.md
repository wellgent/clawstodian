# clawstodian architecture

## Goal

Deliver every job the `ops-daily` / `ops-para` / `ops-clean` packages did, through native OpenClaw primitives, with no package-owned state and no worker choreography.

The design target is a system an operator can monitor, audit, troubleshoot, and trust. Intelligence lives in markdown the agent reads; the harness is thin; every meaningful action is observable by default.

## Design principles

### 1. Programs are authorities; routines are invocations

The package splits behavior from scheduling at the file level.

- A **program** (`programs/<name>.md`) is a durable statement of how the workspace operates in one domain: conventions, authority, approval gates, escalation rules, and the full set of behaviors the agent can perform. Programs are read at session bootstrap via `AGENTS.md` so every agent in the workspace knows how the domain is governed. They change only when the domain's convention changes.
- A **routine** (`routines/<name>.md`) is a thin scheduled invocation: a reference to a program plus the behavior to invoke, a target, a run-report format, worker discipline, and a cron install command. Routines are read only inside cron dispatch. Cadences and report formats change freely without touching programs.

Programs answer *what is true about this domain, always?* Routines answer *what do we run, when, and how do we report it?* Multiple routines can reference the same program, which is the expected shape (for example, both `capture-sessions` and `seal-past-days` routines reference behaviors from the `daily-notes` program).

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

The heartbeat does not execute programs or routines. It is the collaborative maintenance thread between the operator and the agent. Each tick it:

1. Reads workspace state fresh (daily notes, PARA, git status, cron last-run times, recent cron replies).
2. Toggles heartbeat-managed burst workers (`seal-past-days`, `para-extract`) based on their queue state.
3. May `--wake now` `para-align` if mid-week structural drift was reported.
4. Spot-checks health (config drift, missing crons, broken symlinks).
5. Appends a trace line to `memory/heartbeat-trace.md`.
6. Posts a brief status message to the notifications channel - never silent.
7. On longer cadences (daily retrospective, weekly review), produces reflections and proposes improvements.

The heartbeat runs in the agent's main session (the operator's DM with the agent), so the maintenance thread is continuous with whatever the operator and the agent have been discussing. The notifications channel is a separate, read-mostly observability surface: heartbeat status summaries, retrospectives, reviews, and per-routine announcements all land there. Collaboration happens in the DM; observation happens in the channel.

Mixed cadence is managed through a `tasks:` YAML block in `templates/HEARTBEAT.md`: a 2h status sweep (matches the heartbeat interval and fires every tick), a 24h daily retrospective, and a weekly review. Only due tasks fire on a given tick, keeping cost bounded.

This inverts the v0.3 pure-prose dispatcher (which silently dropped ticks when any of seven heartbeat gates short-circuited) toward the `ops-daily` debuggability pattern, and goes further: the agent is not only an orchestrator, it is a collaborative partner with memory. See `docs/heartbeat-config.md` for the rationale and recommended gateway config.

### 4. Four continuity layers

A healthy install carries continuity on four layers, each serving a different need:

- **Per-routine announcement** (detail on demand). Each cron routine posts a single-line run report to the notifications channel on every run that changes something. Quiet runs return `NO_REPLY` and stay silent.
- **Heartbeat notifications posts** (running observability). Every tick posts at least a status line; longer cadences add reflections and reviews. This channel is read-mostly - it's the pane of glass on workspace maintenance activity.
- **Main session history** (collaborative memory). The heartbeat runs in the operator's main DM session with the agent, so past tick outputs, operator replies, and in-flight decisions all accumulate as conversation history. Host-wide session maintenance (compaction) bounds growth.
- **Tick trace file** (forensic record). `memory/heartbeat-trace.md` is an append-only log independent of session state. Greppable and permanent. Survives compaction, session deletion, and anything else that might trim session history.

Silence in any of the four is itself a signal. A dead heartbeat is not ambiguous.

### 5. The workspace is the ledger

No package-owned state files. Git, daily notes, PARA entities, `MEMORY.md`, session transcripts, `memory/session-ledger.md`, and `memory/heartbeat-trace.md` are the only state. Every routine and every heartbeat tick derives what it needs from those artifacts, acts, writes observations back, and forgets.

The `daily-notes` program is the most state-dependent: it needs to know which sessions it has already captured, and how far into each transcript. That state lives in `memory/session-ledger.md` - one markdown section per session, cursor fields advanced in place via narrow `Edit` calls. Cursors advance only after the affected daily-note writes succeed; a partial failure leaves the cursor at the old position so the next tick retries from there. This replaces ops-daily's `capture-state.json` sidecar with a markdown-native file the agent edits with its normal tools.

This is why `isolatedSession: true` and `lightContext: true` are correct for routine runs. Cross-tick memory lives in files, not session history. The workspace bootstrap (`AGENTS.md`, `MEMORY.md`) caches across ticks within OpenClaw's prompt-cache window; program and routine specs are read fresh on every run, so spec updates take effect without re-registering crons.

Note the interaction: `lightContext: true` skips the full workspace bootstrap except `HEARTBEAT.md`. Routines that need `MEMORY.md`, `AGENTS.md`, or PARA reference docs must explicitly read them. Specs in this package do so where needed.

Note also the one OpenClaw config prerequisite: `tools.sessions.visibility: "all"`. Without it, isolated cron sessions cannot see sibling sessions' transcripts, so the `capture-sessions` routine silently captures zero content. This is the sharpest edge in the install and VERIFY explicitly checks it.

### 6. Co-create, do not guess

The agent has judgment but not taste. When placement, filing, or risk is obvious, it acts. When ambiguous, it surfaces: during a session, in chat to the user; under cron dispatch, in the routine's run report to the logs channel.

Per-routine announcements mean the operator sees ambiguities in the channel the same way they see completions. There is no "batch tick summary" to hide inside; every routine speaks for itself.

### 7. Small reversible actions over broad audits

The maintainer prefers one concrete small change over a theoretical sweep. It surfaces emerging projects or misfiled efforts but does not silently promote them. Escalates before anything destructive, risky, or ambiguous.

## Primitive mapping

```
standing authority           AGENTS.md + programs/     (charter + four domain authorities)
collaborative maintainer     HEARTBEAT.md              (reads state, toggles bursts, reflects, converses)
maintainer cadence           heartbeat                 (2h, main session, active hours, full bootstrap)
maintainer continuity        main session history      (conversation with the operator, host-wide compaction)
scheduled invocations        routines/ + cron          (six routines; each a cron job in its own isolated session)
capture state                memory/session-ledger.md  (per-session classification + read cursor)
audit trail                  notifications channel + session transcripts + git + heartbeat-trace.md
workspace memory             memory/, projects/, areas/, resources/, archives/
```

There is no "standing orders" primitive in the OpenClaw codebase; the term in OpenClaw's docs refers to rules written into `AGENTS.md`. clawstodian uses the standing-orders anatomy to structure each program (conventions / authority / approval gates / escalation / behaviors / what NOT to do). The mechanism remains the AGENTS.md file loaded at bootstrap plus cron jobs that dispatch routines with `Read clawstodian/routines/<name>.md and execute.` messages.

## Four programs, six routines

Programs (authorities):

- **`daily-notes`** - canonical daily notes: `memory/YYYY-MM-DD.md` per day. Behaviors: Capture one session's new content; Seal a past-day note.
- **`para`** - PARA knowledge graph: `projects/` / `areas/` / `resources/` / `archives/`. Behaviors: Extract PARA from a sealed note; Align PARA structure.
- **`workspace-tidy`** - workspace cleanliness. Behavior: Walk and tidy.
- **`git-hygiene`** - commit discipline. Behavior: Commit drift.

Routines (scheduled invocations):

- **`capture-sessions`** - daily-notes / Capture one session's new content - heartbeat-toggled burst, every 30m while enabled.
- **`seal-past-days`** - daily-notes / Seal a past-day note - heartbeat-toggled burst, every 30m while enabled.
- **`para-extract`** - para / Extract PARA from a sealed note - heartbeat-toggled burst, every 30m while enabled.
- **`para-align`** - para / Align PARA structure - fixed cron, Sunday 06:00 UTC.
- **`workspace-tidy`** - workspace-tidy / Walk and tidy - always-on cron, every 2h.
- **`git-hygiene`** - git-hygiene / Commit drift - always-on cron, every 30m.

Three execution classes for routines:

- **Always-on cron** - enabled at install time; fires on its schedule; quiet runs return `NO_REPLY`.
- **Fixed cron** - enabled at install time; wall-clock schedule (e.g. Sunday 06:00 UTC).
- **Heartbeat-toggled burst** - starts disabled; heartbeat enables when a queue exists and disables when empty.

Three heartbeat-toggled bursts (`capture-sessions`, `seal-past-days`, `para-extract`) form a pipeline: `capture-sessions` populates daily notes from session transcripts that the agents did not write up in-session; `seal-past-days` closes past-day notes with `para_status: pending`; `para-extract` propagates those sealed notes into PARA entities. Each stage signals readiness via workspace state (ledger entries, frontmatter flags), not in-memory queues. The heartbeat reads those signals once per tick and flips the corresponding crons on or off.

Agents in live sessions remain the primary writers of daily notes per `AGENTS.md` memory-maintenance rules; `capture-sessions` is the backstop that fires only when the session ledger shows un-admitted sessions or stale cursors. On a disciplined workspace where agents update their daily notes in-session, the cron may go days between firings.

## Observability and troubleshooting

A working clawstodian install is debuggable from a small set of surfaces:

1. **Logs channel** - per-routine run reports and heartbeat executive summaries arrive here.
2. **`memory/heartbeat-trace.md`** - append-only tick log, greppable by date.
3. **`openclaw cron list --all`** - which routines are registered, which are enabled, last-run timestamps.
4. **`AGENTS.md` (programs catalog)** - domain authorities.
5. **`HEARTBEAT.md`** - orchestrator loop.
6. **`memory/crons.md`** - operator-readable cron dashboard.

If an operator needs to look at more than that to explain routine behavior, the design has drifted.

## Non-goals

- Full transcript-to-memory coverage. The daily-notes program does its best from `sessions_*` and git; it does not exhaustively reconstruct everything.
- Automatic PARA rewrites. The para program creates and updates obvious placements in extract, applies trivial structural fixes in align; neither reorganizes existing entities without operator direction.
- Hidden state. Any persistent fact the package acts on is a file the operator can read.
- Multi-worker pipelines. Each routine is one cron, one session, one single-line report.
- Auto-archive lifecycle. When inactive projects move from live PARA into `archives/` stays user-managed judgment.
- Custom hooks in the default path. If a future feature needs hooks, it will be documented as opt-in, not baseline.

## Open questions

- Periodic workspace-audit routine: deferred. The install-time smoke test in `VERIFY.md` covers install-time correctness; an audit routine that verifies ongoing delivery is a separate iteration.
- Fixed cron with heartbeat-wake for `para-align` is v0.4's pragmatic solution; a fully declarative "trigger when drift report matches X" would need a queue primitive the package does not have yet.
- `MEMORY.md` + `lightContext: true` interaction: isolated cron sessions do not auto-load `MEMORY.md`; routines that need it read it explicitly. Worth a test before adding a routine that depends on it.
- Notifications channel is intentionally read-mostly. Replies in the channel route to the channel's auto-derived session (OpenClaw routing behavior), not to the main session where the heartbeat runs. The operator collaborates with the agent in the DM, reads the channel for observability.
