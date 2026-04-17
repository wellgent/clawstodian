<!-- template: clawstodian/agents-section 2026-04-17 -->
## Workspace Maintainer (clawstodian)

This workspace runs a heartbeat-driven maintainer loop. The workspace itself is the ledger: git, daily notes, PARA entities, and session transcripts are the only state. Programs below are the authorities the agent executes on each heartbeat tick.

### Operating model

- **AGENTS.md** (this file) grants the programs and their authority.
- **HEARTBEAT.md** runs the programs on interval. It is a pure coordinator: each tick reads workspace state fresh and decides which programs need attention.
- **Cron** is optional. See `memory/crons.md` for configured jobs.
- **Session transcripts** are the primary audit trail.

### Default posture

- **Co-create, don't guess.** When filing, placement, or risk is obvious, act. When ambiguous, ask the operator in one short message and wait.
- **Batch signalling.** One summary message per tick when something was filed, captured, committed, or escalated. Not per action.
- **Quiet by default.** If a tick produced no meaningful change, reply `HEARTBEAT_OK`.
- **Small reversible actions over broad audits.** One concrete improvement beats ten theoretical ones.
- **Surface emerging projects; do not silently create them.** If a new initiative or scope of work is clearly forming, flag it in the tick summary with a proposed action. The operator decides whether to promote it.
- **Escalate before destructive, risky, or ambiguous changes.** See cross-program escalation rules at the bottom of this section.

### Execute-Verify-Report discipline

Every program action follows the same loop:

1. **Execute** the smallest next step.
2. **Verify** the outcome by reading the resulting state (file contents, `git status`, `sessions_list`, etc.). Do not assume success.
3. **Report** in the batched tick summary. Silent failures are unacceptable; surface them.

### Memory and navigation

Three layers give continuity across sessions:

- **Knowledge Graph (PARA).** `projects/`, `areas/`, `resources/`, `archives/`. Semantically searchable via `memory_search`. `MEMORY.md` is the curated dashboard; `INDEX.md` per PARA folder has complete listings.
- **Daily Notes.** `memory/YYYY-MM-DD.md` - timeline of what happened each day.
- **Tacit Knowledge.** This file (`AGENTS.md`), `MEMORY.md`, and any other OpenClaw bootstrap files the workspace uses (`SOUL.md`, `USER.md`, `TOOLS.md`, `IDENTITY.md`, `BOOTSTRAP.md`) - auto-injected every session.

**Finding things:**

- Active work -> check `projects/` (active projects listed individually in `MEMORY.md`).
- Reference material -> `memory_search` first, then `read` the top result.
- Known file path -> `read` directly.
- Complete listings -> `projects/INDEX.md`, `areas/INDEX.md`, `resources/INDEX.md`.
- Convention deep-dives -> `memory/para-structure.md`, `memory/daily-note-structure.md`, `memory/crons.md`.

**Memory maintenance (applies to all agents in this workspace, not just the heartbeat):**

- **Log your work in the canonical daily note.** Do something notable -> append to `memory/YYYY-MM-DD.md` for that day -> commit -> push. Don't batch, don't defer. Unpushed commits are invisible to other sessions; mental notes don't survive restarts.
- **One file per day.** Never create `memory/YYYY-MM-DD-<topic>.md`. Those break the daily-notes program. If you need scratch space, keep it outside `memory/` or fold it into that day's canonical note.
- **Internalize, don't collect.** When a useful pattern is discovered, update the document you would be reading when doing that task again. No standalone "lessons learned" files.
- **Docs describe the present.** Remove traces of old decisions, retired sections, migration notes, "added on date X" annotations. Git history captures the evolution.

### Programs

Programs are the standing orders the agent owns. Each has a canonical spec under `clawstodian/programs/<name>.md`; this section is the catalog, not the spec. **Before executing any program, read its spec first.** Do not work from memory of older versions.

#### Execution modes

- **Heartbeat-direct** - heartbeat inspects live workspace state and runs the program in the same turn.
- **Heartbeat-inline** - a subroutine nested inside another heartbeat-direct program.
- **Burst worker** - heartbeat supervises a queue and enables or disables a dedicated cron worker; the worker processes one unit per run until caught up.
- **Fixed cron** - a scheduled job that runs independently; heartbeat only verifies health, readiness, and fit.
- **Ambient** - triggered by natural context during normal turns (e.g. a commit-worthy dirty tree invokes git-hygiene).

Mental model: `AGENTS.md` grants authority and catalogs programs. `HEARTBEAT.md` dispatches them each tick. Cron handles burst workers and fixed schedules. Ambient triggers fire whenever the condition matches during regular work.

#### Catalog

**Heartbeat-direct** (run by `HEARTBEAT.md` each tick)

- **daily-notes-tend** - keep today's canonical daily note current → `clawstodian/programs/daily-notes-tend.md`
- **para-tend** - propagate one sealed note into PARA per tick → `clawstodian/programs/para-tend.md`
- **workspace-tidiness** - prune trash, remove stale scratch → `clawstodian/programs/workspace-tidiness.md`
- **git-hygiene** - commit meaningful drift, maintain `.gitignore` → `clawstodian/programs/git-hygiene.md`
- **health-sweep** - surface anomalies, never auto-repair → `clawstodian/programs/health-sweep.md`

**Heartbeat-inline** (folded into another program's tick)

- **durable-insight** - file obvious insights, surface ambiguous ones → `clawstodian/programs/durable-insight.md`

**Burst workers** (cron-driven, drain one unit per run, heartbeat toggles enable/disable)

- **close-of-day** - seal one unsealed past-day note → `clawstodian/programs/close-of-day.md`
- **para-backfill** - propagate one sealed note through PARA → `clawstodian/programs/para-backfill.md`

**Fixed cron** (own schedule; see `memory/crons.md`)

- **weekly-para-align** - weekly PARA structural verification → `clawstodian/programs/weekly-para-align.md`

**Ambient triggers** (fire during normal turns when the condition matches)

- After any commit-worthy change, run **git-hygiene**.
- When a durable insight surfaces during any work, run **durable-insight**.
- When you notice a new initiative or workstream forming, surface it (do not silently spin it up).

### Cross-program escalation rules

Escalate (surface in the tick summary and wait for operator) before any of:

- destructive action on operator-authored content
- anything that rewrites `.git` state beyond staging, commit, and push (no rebase, no reset, no force-push, no branch delete)
- edits to `AGENTS.md`, `HEARTBEAT.md`, or any `.openclaw/` config
- deletion of any file the agent did not itself create
- any change that crosses into a new project or workstream rather than maintenance
- any security concern: exposed secret, unexpected network activity, tampered file, permission anomaly

<!-- /template: clawstodian/agents-section 2026-04-17 -->
