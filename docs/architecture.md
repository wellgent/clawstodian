# clawstodian architecture

## Goal

Deliver every job the `ops-daily` / `ops-para` / `ops-clean` packages did, through native OpenClaw primitives executed by the main-session agent, with no package-owned state and no worker choreography.

The design target is a system an operator can monitor, audit, troubleshoot, and trust. Intelligence lives in markdown the agent reads; the harness is thin.

## Design principles

### 1. Native primitives over invented machinery

Use what OpenClaw ships:
- `AGENTS.md` for standing authority (loaded first in context).
- `HEARTBEAT.md` for the recurring execution loop.
- Heartbeat for the quiet interval cadence.
- Cron for wall-clock-bound bursts, only when they earn their keep.
- Session transcripts for auditability.
- Session tools (`sessions_list`, `sessions_history`) and raw disk JSONL for transcript access.

Avoid building a parallel orchestration layer.

### 2. Heartbeat is the orchestrator

The heartbeat runs always, on a cadence, and drives the six programs. Cron is optional. Two patterns ship:

- **Demand-driven burst** (`close-of-day`): starts disabled, enabled by the heartbeat when work accumulates, processes one unit per run, self-disables when the queue is empty.
- **Scheduled job** (`weekly-para-align`): plain cron, runs at its slot, done.

This inverts the ops-* model (scan cron as orchestrator, demand-driven worker crons). One loop, with bursts as exceptions.

### 3. The workspace is the ledger

No package-owned state files. Git, daily notes, PARA entities, `MEMORY.md`, and session transcripts are the only state. Every heartbeat tick derives what it needs from those artifacts, acts, writes observations back to those artifacts, and forgets.

This is why `isolatedSession: true` is correct: cross-tick memory does not live in a session history; it lives in files. The full workspace bootstrap (`AGENTS.md`, `MEMORY.md`, etc.) loads each tick and caches across ticks, so the agent always has its authorities and workspace map at the cost of a single cached bootstrap per cache window, not one reload per tick.

### 4. Co-create, do not guess

The agent has judgment but not taste. When placement, filing, or risk is obvious, it acts. When ambiguous, it asks the operator in one short question. Signalling is batched one summary per tick, not one message per action.

This is the hardest invariant to preserve as programs grow; it is the one that makes the difference between a quiet colleague and an over-eager robot.

### 5. Small reversible actions over broad audits

The maintainer prefers one concrete small change over a theoretical sweep. It surfaces emerging projects or misfiled efforts but does not silently promote them. Escalates before anything destructive, risky, or ambiguous.

### 6. Quiet by default

If a tick produced no meaningful change, reply `HEARTBEAT_OK`. The maintainer earns operator trust by not being noisy.

## Primitive mapping

```
standing authority       AGENTS.md         (charter + six programs)
recurring execution      HEARTBEAT.md      (tasks block)
interval cadence         heartbeat         (2h default, active hours, isolated session)
wall-clock jobs          cron              (opt-in; demand-driven or plain scheduled)
audit trail              session transcripts + git history
workspace memory         memory/, projects/, areas/, resources/, archives/
```

There is no "standing orders" primitive in the OpenClaw codebase; the term in OpenClaw's docs refers to rules written into `AGENTS.md`. clawstodian uses the standing-orders anatomy (authority / trigger / approval gate / escalation / execution steps / what NOT to do) to structure each program, but the mechanism remains the AGENTS.md file loaded at session bootstrap.

## The six programs

Each program has a single-page definition in `AGENTS-SECTION.md` and a heartbeat task in `HEARTBEAT-SECTION.md` that executes it.

| Program | Heartbeat task | Cron recipe | Replaces |
| - | - | - | - |
| Daily notes | `daily-notes-tend` (2h) | `close-of-day` (opt-in) | ops-daily scan/capture/polish |
| Durable insight capture | `daily-notes-tend` (2h) | none | ops-daily polish editorial layer |
| PARA graph | `para-tend` (4h) | `weekly-para-align` (opt-in) | ops-para extract/distill/verify/align |
| Workspace tidiness | `workspace-sweep` (6h) | none | ops-clean sweep |
| Git hygiene | `workspace-sweep` (6h) | none | ops-clean git |
| Health sweep | `workspace-sweep` (6h) | none | (new; distilled from all three) |

The tidiness / git / health programs share a heartbeat tick because they all inspect the workspace. They remain distinct programs in `AGENTS.md` for clarity of authority and boundaries, but they batch for efficiency.

## Observability and troubleshooting

A working clawstodian install is debuggable from a small set of surfaces:

1. `AGENTS.md` - program definitions and authority.
2. `HEARTBEAT.md` - execution loop.
3. `memory/crons.md` - cron recipe state.
4. Recent session transcripts.
5. `openclaw cron list` - cron job status.

If an operator needs to look at more than that to explain routine behavior, the design has drifted.

## Non-goals

- Full transcript-to-memory coverage. The daily-notes program does its best from `sessions_*` and git; it does not exhaustively reconstruct everything.
- Automatic PARA rewrites. The PARA program creates and updates; it never reorganizes existing entities without operator direction.
- Hidden state. Any persistent fact the package acts on is a file the operator can read.
- Multi-worker pipelines. One loop, one agent per tick, no orchestration choreography.
- Custom hooks in the default path. If a future feature needs hooks, it will be documented as opt-in, not baseline.

## Open questions

- Should the install flow detect a workspace still using `ops-daily` / `ops-para` / `ops-clean` and offer a migration plan, or only support greenfield installs? (Current stance: surface the overlap, let the operator decide.)
