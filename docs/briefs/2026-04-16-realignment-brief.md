# clawstodian realignment brief

Date: 2026-04-16

## Why this brief exists

An earlier draft framed clawstodian as a minimal "quiet workspace steward." That shape under-delivered against the actual problem: workspaces that previously ran `ops-daily`, `ops-para`, and `ops-clean` still need every job those packages did - daily notes, durable insight capture, PARA knowledge graph, workspace tidiness, git hygiene, health monitoring. The question is how to deliver those jobs via native OpenClaw primitives instead of cron-driven Python scripts with state files and worker choreography.

This brief resets the scope to cover all the ops-* goals through a heartbeat-driven program model.

## Corrected scope

clawstodian is a sharable OpenClaw agent package that installs:

- a workspace maintainer charter in `AGENTS.md` that declares six programs with authority, trigger, approval gate, escalation, execution steps, and boundaries
- a `HEARTBEAT.md` tasks block that executes and orchestrates those programs
- opt-in cron routines for work that benefits from wall-clock timing, managed dynamically by the heartbeat
- reusable reference templates for the workspace (`memory/para-structure.md`, `memory/daily-note-structure.md`, `MEMORY.md`, `memory/crons.md`)
- an agent-driven install flow so a running agent session can set the whole thing up from a single paste-line

The design is still minimal, but minimal in the right places. The programs themselves are substantive; the machinery around them is thin.

## The six programs

1. **Daily notes.** One canonical `memory/YYYY-MM-DD.md` per calendar day with activity. Sources: `sessions_list` + `sessions_history` tools, raw transcript JSONL for fidelity when sealing, `git log`, workspace diffs, the agent's own observations. Replaces `ops-daily` scan / capture / polish.

2. **Durable insight capture.** When something meaningful happened, write or update the appropriate durable note. Judgment-driven. Proactive but batched: one summary message per tick listing what was filed. Consults the user when placement is ambiguous.

3. **PARA knowledge graph.** Extracts projects / areas / resources / archives entities from daily notes. Paths follow the established workspace convention: `projects/<name>/README.md`, `areas/people/<slug>.md`, `areas/companies/<slug>.md`, `resources/<slug>.md`, `archives/…`. Auto-creates when placement is obvious; consults the user when ambiguous. Replaces `ops-para` extract / distill / verify / align.

4. **Workspace tidiness.** Empty dirs, orphans, stale run-logs, `.gitignore` drift, archive hygiene. Does obvious things directly; suggests for anything unfamiliar. Replaces `ops-clean` sweep.

5. **Git hygiene.** Commits meaningful drift, one concern per commit, never `git add -A`, no AI attribution, no `--no-verify`. Adds obvious ephemeral patterns to `.gitignore`; asks the user for non-obvious cases. Replaces `ops-clean` git.

6. **Health sweep.** Surfaces workspace anomalies with likely causes: failed cron runs, stale configs, broken symlinks, template drift. Proposes resolution; does not auto-repair configs silently.

Each program is defined in `AGENTS-SECTION.md` using the standing-orders anatomy (authority / trigger / approval gate / escalation / execution steps / what NOT to do). The heartbeat tasks in `HEARTBEAT-SECTION.md` are the operational side that fires them.

## Cron is optional; heartbeat is the orchestrator

The heartbeat is always-on (on a cadence) and drives all six programs. Cron is opt-in. Two patterns ship:

- **Demand-driven burst** - `close-of-day` starts disabled, is enabled by the heartbeat when past-day notes accumulate, runs `every 30m` while enabled, seals one note per run, self-disables when the queue is empty.
- **Scheduled job** - `weekly-para-align` is a plain `Sunday 06:00` cron; runs at its slot, reports, done.

Neither is required. Both can be skipped by workspaces that prefer pure heartbeat.

## Co-creation discipline

The agent is a scribe, not an architect. The workspace structure belongs to the operator. That implies concrete rules the programs must follow:

- **When the placement is obvious, just go for it.** A new person mentioned with clear context lands in `areas/people/<slug>.md`. A git commit for a clear bug fix commits itself.
- **When the placement is ambiguous, ask.** A resource that could belong under multiple folders, a new top-level directory of unknown origin, a large binary blob - surface it before deciding.
- **When you act, inform in batch.** One short "filed X, Y, Z this tick" message per tick beats per-action chatter.
- **When you surface a problem, propose one or two resolution paths.** Do not just alert; collaborate on resolution.

## Distribution model

Borrowed in spirit from `gbrain`: agent-driven install. The operator tells their running agent:

> Install clawstodian into my workspace. Follow `INSTALL_FOR_AGENTS.md` in the clawstodian repo.

The agent locates (or clones) the package, reads `INSTALL_FOR_AGENTS.md`, surveys the target workspace, proposes a merge plan for `AGENTS.md` / `HEARTBEAT.md` / reference templates, asks any gating questions, applies on approval, applies the heartbeat config snippet, and runs a verification pass. Never overwrites operator content silently.

## Deliverables for this iteration

- `AGENTS-SECTION.md` with charter plus six programs in full standing-orders anatomy.
- `HEARTBEAT-SECTION.md` with tasks block that runs and orchestrates programs.
- `INSTALL_FOR_AGENTS.md` with the agent-driven install flow.
- `templates/` with `para-structure.md`, `daily-note-structure.md`, `MEMORY.md`, `crons.md`.
- `cron-routines/` with `close-of-day.md` and `weekly-para-align.md`.
- Updated `README.md`, `docs/architecture.md`, `CHANGELOG.md`, `VERSION`.
- Removed: `setup.sh`, `SETUP.md`, `templates/HEARTBEAT.md` (superseded).

## Acceptance criteria

- A workspace owner can paste one line into their agent and end up with a working install, without running shell commands themselves.
- The six programs are each explainable from one page of `AGENTS-SECTION.md`.
- The heartbeat alone, with zero crons enabled, accomplishes every ops-* goal at a slower cadence.
- Adding the two cron routines tightens close-of-day sealing and weekly PARA alignment without changing the program definitions.
- No package-owned state files exist anywhere. The workspace's git tree, daily notes, PARA entities, and session transcripts are the only ledger.
- The install never overwrites operator content silently; diffs + confirmation only.
- The agent consults the operator whenever placement, filing, or risk is ambiguous; acts on judgment when it is obvious.
- Signalling is batched per heartbeat tick, not per action.
