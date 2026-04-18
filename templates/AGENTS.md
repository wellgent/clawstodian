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

This workspace runs four maintenance **programs** that define how the workspace operates, and six **routines** that schedule those programs to run on cron as a catch-up safety net. Programs are the durable authorities; routines are scheduled invocations. The workspace itself is the ledger - git, daily notes, PARA entities, and session transcripts are the only state.

### Operating model

- **Programs** (`clawstodian/programs/<name>.md`) describe how a workspace domain is governed - conventions, authority, approval gates, escalation, behaviors. Agents follow programs during normal sessions when the situation applies, and cron-dispatched routines follow the same programs on a schedule.
- **Routines** (`clawstodian/routines/<name>.md`) are thin scheduled invocations. Each routine references a program, picks a specific behavior, defines a target and a run-report format, and runs as a cron job.
- **AGENTS.md** (this file) catalogs the programs.
- **HEARTBEAT.md** runs the collaborative maintainer thread. Each tick the agent reviews workspace state, toggles burst-worker routines, spot-checks health, and posts to the maintainer channel. Mixed cadence: a short status sweep every 2h, a daily retrospective, a weekly review. The heartbeat runs in a dedicated persistent session so the operator and the agent carry a continuous thread across ticks. It does NOT execute programs; each routine does that on its own cron.
- **Session transcripts and `memory/heartbeat-trace.md`** are the primary audit trail.

### Default posture

- **Co-create, don't guess.** When filing, placement, or risk is obvious, act. When ambiguous, surface (in-session: ask the operator in chat; via cron: include in the routine's run report so the operator sees it in the logs channel).
- **Per-routine announce.** Each routine emits a single-line run report. The cron runner delivers it to the maintainer channel as an announcement. Quiet runs return `NO_REPLY` and stay silent.
- **Heartbeat never goes silent.** Every heartbeat tick posts at least a status one-liner to the maintainer channel, plus occasional longer reflections (daily retrospective, weekly review). Silence means a broken orchestrator, never a healthy one.
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

**Memory maintenance (applies to all agents in this workspace, not just clawstodian-driven runs):**

- **Log your work in the canonical daily note.** Do something notable -> append to `memory/YYYY-MM-DD.md` for that day -> commit -> push. Don't batch, don't defer. Unpushed commits are invisible to other sessions; mental notes don't survive restarts.
- **One file per day.** Avoid creating `memory/YYYY-MM-DD-<topic>.md` unless necessary for a specific handoff. The daily-note routine will merge any such siblings into the canonical note on its next run.
- **Internalize, don't collect.** When a useful pattern is discovered, update the document you would be reading when doing that task again. No standalone "lessons learned" files.
- **Docs describe the present.** Remove traces of old decisions, retired sections, migration notes, "added on date X" annotations. Git history captures the evolution.

### Programs

Programs are the domain authorities for this workspace. Each is a canonical spec under `clawstodian/programs/<name>.md`; this section is the catalog. **Before acting in a domain, read the program's spec first.** Do not work from memory of older versions.

- **daily-notes** - canonical daily notes: one `memory/YYYY-MM-DD.md` per calendar day capturing activity, decisions, and context. Covers tending today's note, merging slug siblings, sealing past-day notes, and frontmatter discipline. Spec: `clawstodian/programs/daily-notes.md`.
- **para** - the PARA knowledge graph: `projects/`, `areas/`, `resources/`, `archives/` extracted from daily activity and aligned against `memory/para-structure.md`. Covers entity extraction from sealed notes, structural and semantic alignment, and MEMORY.md dashboard currency. Spec: `clawstodian/programs/para.md`.
- **workspace-tidy** - workspace cleanliness: trash removal, misplaced file relocation, `.gitignore` maintenance for ephemeral artifacts. Spec: `clawstodian/programs/workspace-tidy.md`.
- **git-hygiene** - commit discipline: stage-by-path commits with clear messages, immediate push, `.gitignore` maintenance, and a working tree never left in a surprising state. Spec: `clawstodian/programs/git-hygiene.md`.

Any agent in this workspace follows a program whenever the situation in that domain applies - committing work after a session, tending today's daily note, filing an insight into PARA. Routines (below) schedule the same programs to run as cron-dispatched catch-up.

### Routines

Routines are scheduled cron invocations that execute program behaviors on a cadence. They catch what agents missed during normal sessions. Each routine has a canonical spec under `clawstodian/routines/<name>.md`; the workspace cron dashboard is `memory/crons.md`.

Two execution classes:

- **Always-on cron** - runs on its schedule regardless of state. Quiet runs return `NO_REPLY`.
- **Heartbeat-toggled burst** - starts disabled. The heartbeat orchestrator enables when a queue exists and disables when empty.

Current routines:

- **daily-note** (always-on, every 30m) - invokes daily-notes: tend today's note.
- **seal-past-days** (burst) - invokes daily-notes: seal a past-day note.
- **para-extract** (burst) - invokes para: extract PARA from a sealed note.
- **para-align** (fixed cron, Sunday 06:00 UTC) - invokes para: align PARA structure.
- **workspace-tidy** (always-on, every 2h) - invokes workspace-tidy: walk and tidy.
- **git-hygiene** (always-on, every 30m) - invokes git-hygiene: commit drift.

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
