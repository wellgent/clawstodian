<!-- Template for a workspace AGENTS.md that adopts clawstodian.
     Copy this to the workspace root as AGENTS.md, or merge its
     content into an existing AGENTS.md. Add persona, project-
     specific rules, and anything else above or below the
     clawstodian section as fits your workspace.
     The <!-- template: ... --> marker lets the install flow detect
     whether the clawstodian section is up to date. You can drop
     the markers if you prefer a plain file; updates then become a
     manual merge. -->

<!-- template: clawstodian/agents 2026-04-18 -->
## Workspace Maintainer (clawstodian)

This workspace runs four maintenance **programs** that define how the workspace operates, and six **routines** that schedule those programs to run on cron as a catch-up safety net. Programs are the durable authorities; routines are scheduled invocations. The workspace itself is the ledger - git, daily notes, PARA entities, session transcripts, and `memory/session-ledger.md` are the only state.

### Operating model

- **Programs** (`clawstodian/programs/<name>.md`) describe how a workspace domain is governed - conventions, authority, approval gates, escalation, behaviors. Agents follow programs during normal sessions when the situation applies, and cron-dispatched routines follow the same programs on a schedule.
- **Routines** (`clawstodian/routines/<name>.md`) are thin scheduled invocations. Each routine references a program, picks a specific behavior, defines a target and a run-report format, and runs as a cron job.
- **AGENTS.md** (this file) catalogs the programs.
- **HEARTBEAT.md** runs the collaborative maintainer thread. Each tick the agent reviews workspace state, toggles burst-worker routines, spot-checks health, and posts to the notifications channel. Mixed cadence: a short status sweep every 2h, a daily retrospective, a weekly review. The heartbeat runs in the agent's main session (the same DM the operator uses), so the maintenance thread is continuous with the operator's ongoing conversation with the agent. It does NOT execute programs; each routine does that on its own cron.
- **Session transcripts and `memory/heartbeat-trace.md`** are the primary audit trail.

### Default posture

- **Co-create, don't guess.** When filing, placement, or risk is obvious, act. When ambiguous, surface (in-session: ask the operator in chat; via cron: include in the routine's run report so the operator sees it in the logs channel).
- **Per-routine announce.** Each routine emits a multi-line scannable run report to the notifications channel on every firing, plus a detailed run-report file to `memory/runs/<routine>/<ts>.md`. Even a quiet firing ("nothing to do") produces both - silence in the channel means the cron did not fire, never "cron fired, found nothing".
- **Heartbeat never goes silent.** Every heartbeat tick posts at least a status one-liner to the notifications channel, plus occasional longer reflections (daily retrospective, weekly review). Silence means a broken orchestrator, never a healthy one.
- **Small reversible actions over broad audits.** One concrete improvement beats ten theoretical ones.
- **Surface emerging projects; do not silently create them.** If a new initiative is clearly forming, flag it rather than spinning it up. The operator decides whether to promote it.
- **Escalate before destructive, risky, or ambiguous changes.** See cross-program escalation rules at the bottom of this section.

### Execute-Verify-Report discipline

Every program action follows the same loop:

1. **Execute** the smallest next step.
2. **Verify** the outcome by reading the resulting state (file contents, `git status`, `sessions_list`, etc.). Do not assume success.
3. **Report** - during a session, to the user in chat; via cron, in the routine's single-line run report. Silent failures are unacceptable; surface them.

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
- Capture state (internal; written by `sessions-capture`) -> `memory/session-ledger.md`. Format spec lives in `memory/daily-note-structure.md` under the "Session Ledger" section.
- Per-routine run reports -> `memory/runs/<routine-name>/<timestamp>.md`. Each cron firing that does meaningful work writes a detail file here; the channel summary always ends with a pointer. Pruned after 30 days by `workspace-clean`.

**Memory maintenance (applies to all agents in this workspace, not just clawstodian-driven runs):**

- **Log your work in the canonical daily note.** Do something notable -> append to `memory/YYYY-MM-DD.md` for that day -> commit -> push. Don't batch, don't defer. Unpushed commits are invisible to other sessions; mental notes don't survive restarts. You are the primary writer of daily notes; `sessions-capture` is only the backstop that catches what you miss.
- **One file per day.** Avoid creating `memory/YYYY-MM-DD-<topic>.md` unless necessary for a specific handoff. The `sessions-capture` routine will merge any such siblings into the canonical note when it next processes a session touching today.
- **Internalize, don't collect.** When a useful pattern is discovered, update the document you would be reading when doing that task again. No standalone "lessons learned" files.
- **Docs describe the present.** Remove traces of old decisions, retired sections, migration notes, "added on date X" annotations. Git history captures the evolution.

### Programs

Programs are the domain authorities for this workspace. Each is a canonical spec under `clawstodian/programs/<name>.md`; this section is the catalog. **Before acting in a domain, read the program's spec first.** Do not work from memory of older versions.

- **daily-notes** - canonical daily notes: one `memory/YYYY-MM-DD.md` per calendar day capturing activity, decisions, and context. Covers tending today's note, merging slug siblings, sealing past-day notes, and frontmatter discipline. Spec: `clawstodian/programs/daily-notes.md`.
- **para** - the PARA knowledge graph: `projects/`, `areas/`, `resources/`, `archives/` extracted from daily activity and aligned against `memory/para-structure.md`. Covers entity extraction from sealed notes, structural and semantic alignment, and MEMORY.md dashboard currency. Spec: `clawstodian/programs/para.md`.
- **workspace** - workspace tree outside PARA: trash removal, misplaced file relocation, `.gitignore` maintenance for ephemeral artifacts, 30-day run-report pruning. Spec: `clawstodian/programs/workspace.md`.
- **repo** - git repository discipline: stage-by-path commits with clear messages, immediate push, `.gitignore` maintenance, and a working tree never left in a surprising state. Spec: `clawstodian/programs/repo.md`.

Any agent in this workspace follows a program whenever the situation in that domain applies - committing work after a session, tending today's daily note, filing an insight into PARA. Routines (below) schedule the same programs to run as cron-dispatched catch-up.

### Routines

Routines are scheduled cron invocations that execute program behaviors on a cadence. They catch what agents missed during normal sessions. Each routine has a canonical spec under `clawstodian/routines/<name>.md`; the workspace cron dashboard is `memory/crons.md`.

Two execution classes:

- **Scheduled** - enabled at install, fires on its wall-clock schedule. No self-disable.
- **Heartbeat-toggled burst** - starts disabled, heartbeat enables when a queue exists, self-disables when drained.

Every firing in both classes produces a run-report file under `memory/runs/<routine>/<ts>.md` and a channel post. No silent firings.

Current routines:

- **sessions-capture** (burst, every 30m while enabled) - invokes daily-notes: capture one session's unread JSONL into the appropriate daily notes. Heartbeat enables when the ledger has un-admitted sessions or stale cursors. Agents in-session remain the primary writers; this cron is the backstop.
- **daily-seal** (burst, every 30m while enabled) - invokes daily-notes: seal one past-day note per firing. Heartbeat enables when past-active notes with `capture_status: done` exist.
- **para-extract** (burst, every 30m while enabled) - invokes para: extract PARA from one sealed note per firing. Heartbeat enables when sealed notes with `para_status: pending` exist.
- **para-align** (scheduled, Sunday 06:00 UTC) - invokes para: align PARA structure across the full graph.
- **workspace-clean** (scheduled, Sunday 07:00 UTC) - invokes workspace: walk and tidy.
- **git-clean** (scheduled, 01:00 and 11:00 UTC daily) - invokes repo: commit drift as a backstop for agents who commit themselves in-session.

See `memory/crons.md` for schedules and current enable state.

### Cross-program escalation rules

Any program action that crosses these lines escalates - surface (in reply or run report) and do NOT proceed without explicit operator confirmation:

- destructive action on operator-authored content
- anything that rewrites `.git` state beyond staging, commit, and push (no rebase, no reset, no force-push, no branch delete)
- edits to `AGENTS.md`, `HEARTBEAT.md`, or any `.openclaw/` config
- deletion of any file the agent did not itself create
- any change that crosses into a new project or workstream rather than maintenance
- any security concern: exposed secret, unexpected network activity, tampered file, permission anomaly

<!-- /template: clawstodian/agents 2026-04-18 -->
