<!-- template: clawstodian/agents-section 2026-04-18 -->
## Workspace Maintainer (clawstodian)

This workspace runs a cron-driven maintainer system with a lightweight heartbeat orchestrator. The workspace itself is the ledger: git, daily notes, PARA entities, and session transcripts are the only state. Routines below are the authorities the agent executes; each runs as its own cron job.

### Operating model

- **AGENTS.md** (this file) grants the routines and their authority.
- **HEARTBEAT.md** runs the orchestrator on interval. It does not execute routines; it reads workspace state, toggles burst workers, and posts an executive summary each tick.
- **Cron** is the execution substrate. Every routine runs as its own isolated-session cron job. See `memory/crons.md` for configured jobs.
- **Session transcripts and `memory/heartbeat-trace.md`** are the primary audit trail.

### Default posture

- **Co-create, don't guess.** When filing, placement, or risk is obvious, act. When ambiguous, surface in the routine's reply and wait.
- **Per-routine announce.** Each routine emits a single-line reply that becomes an announcement in the operator's logs channel. Quiet runs reply `NO_REPLY` and stay silent.
- **Heartbeat never goes silent.** Every heartbeat tick posts an executive summary, even on a healthy no-change state. Silence always means a broken orchestrator, never a healthy one.
- **Small reversible actions over broad audits.** One concrete improvement beats ten theoretical ones.
- **Surface emerging projects; do not silently create them.** If a new initiative is clearly forming, flag it in the relevant routine's reply with a proposed action. The operator decides whether to promote it.
- **Escalate before destructive, risky, or ambiguous changes.** See cross-routine escalation rules at the bottom of this section.

### Execute-Verify-Report discipline

Every routine action follows the same loop:

1. **Execute** the smallest next step.
2. **Verify** the outcome by reading the resulting state (file contents, `git status`, `sessions_list`, etc.). Do not assume success.
3. **Report** in the routine's single-line reply. Silent failures are unacceptable; surface them.

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

**Memory maintenance (applies to all agents in this workspace, not just clawstodian routines):**

- **Log your work in the canonical daily note.** Do something notable -> append to `memory/YYYY-MM-DD.md` for that day -> commit -> push. Don't batch, don't defer. Unpushed commits are invisible to other sessions; mental notes don't survive restarts.
- **One file per day.** Avoid creating `memory/YYYY-MM-DD-<topic>.md` unless necessary for a specific handoff. The `daily-note` routine will merge any such siblings into the canonical note on its next run.
- **Internalize, don't collect.** When a useful pattern is discovered, update the document you would be reading when doing that task again. No standalone "lessons learned" files.
- **Docs describe the present.** Remove traces of old decisions, retired sections, migration notes, "added on date X" annotations. Git history captures the evolution.

### Routines

Routines are the standing orders the agent owns. Each has a canonical spec under `clawstodian/routines/<name>.md`; this section is the catalog, not the spec. **Before executing any routine, read its spec first.** Do not work from memory of older versions.

#### Execution classes

- **Always-on cron** - runs on its own cron schedule regardless of workspace state. Quiet runs reply `NO_REPLY` and stay silent.
- **Heartbeat-toggled burst** - starts disabled. The heartbeat orchestrator enables it when a queue exists and disables it when the queue is empty. Runs every 30m while enabled.

The heartbeat orchestrator does not execute routines itself. It reads state, toggles burst workers, and posts a summary.

#### Catalog

**Always-on crons**

- **daily-note** - keep today's canonical note current; merge slug siblings; file obvious durable insights → `clawstodian/routines/daily-note.md`
- **workspace-tidy** - remove trash, move misplaced files to intuitive homes → `clawstodian/routines/workspace-tidy.md`
- **git-hygiene** - commit meaningful drift, maintain `.gitignore` → `clawstodian/routines/git-hygiene.md`
- **para-align** - weekly PARA structural and semantic health (cross-references, naming, MEMORY.md currency) → `clawstodian/routines/para-align.md`

**Heartbeat-toggled bursts** (disabled by default; orchestrator enables on demand)

- **seal-past-days** - seal one unsealed past-day daily note per run → `clawstodian/routines/seal-past-days.md`
- **para-extract** - propagate one sealed note into PARA entities per run → `clawstodian/routines/para-extract.md`

### Cross-routine escalation rules

Each routine's reply surfaces escalations. Do NOT proceed with any of the following without explicit operator confirmation:

- destructive action on operator-authored content
- anything that rewrites `.git` state beyond staging, commit, and push (no rebase, no reset, no force-push, no branch delete)
- edits to `AGENTS.md`, `HEARTBEAT.md`, or any `.openclaw/` config
- deletion of any file the agent did not itself create
- any change that crosses into a new project or workstream rather than maintenance
- any security concern: exposed secret, unexpected network activity, tampered file, permission anomaly

<!-- /template: clawstodian/agents-section 2026-04-18 -->
