# Changelog

## 0.4.0-draft - 2026-04-18

Program/routine split, cron-per-routine inversion, three-layer observability. v0.3 kept the heartbeat executing five routines in a pure-prose dispatcher; in live use a gateway restart produced a silent heartbeat failure with no detectable signal. v0.4 separates domain authorities (programs) from scheduled invocations (routines), pushes execution onto cron (the self-observing substrate), and shrinks the heartbeat to a pure orchestrator that never goes silent.

The v0.4 draft went through several iterations inside the `2026-04-18` day. The first pass merged behavior and scheduling into a single set of "routines." The second pass separated them: behavior lives in `programs/` (domain authorities), scheduling lives in `routines/` (thin cron dispatchers). The third pass stripped install/verify/uninstall sections out of routine specs and extracted them into top-level `INSTALL.md`, `VERIFY.md`, and `UNINSTALL.md` so routines stay purely behavioral. The fourth pass reshaped the heartbeat from the prior isolated, pure-orchestrator model to a collaborative-maintainer model: heartbeat runs in the agent's main session (where the operator already collaborates with the agent by DM) and posts to a dedicated notifications channel for observability. Mixed cadence via a `tasks:` block in `templates/HEARTBEAT.md` (2h status, daily retrospective, weekly review). The final shape is what this entry describes.

Added:
- `programs/` directory with four domain authorities: `daily-notes.md`, `para.md`, `workspace-tidy.md`, `git-hygiene.md`. Each is a thick spec describing conventions, authority, approval gates, escalation, and named behaviors. Programs are read at session bootstrap via `AGENTS.md` so any agent in the workspace follows the same domain rules whether invoked in-session or via cron.
- `docs/heartbeat-config.md` (new) - authoritative reference for the heartbeat gateway config: session model trade-offs, field-by-field rationale, `tasks:` interaction, channel binding for bidirectional flow, cost profile, troubleshooting.
- `memory/heartbeat-trace.md` append-only tick log as the forensic record that proves heartbeat fired.
- Executive summary to logs channel on every heartbeat tick (including healthy no-change ticks).
- Per-routine announcements to the logs channel via `--announce --channel --to` on every cron.
- `VERIFY.md` standalone verification doc: markers, both symlinks, programs + routines reachable, templates, cron registrations, heartbeat config sanity, trace file. Idempotent; can be run after install or any time. `INSTALL.md` references it as its final step.
- `UNINSTALL.md` standalone removal doc: disable and remove crons, remove symlinks, strip sections, revert heartbeat config, what to leave alone.
- `para_status` field documented in `templates/daily-note-structure.md` as the PARA extraction queue marker (`pending -> done`).
- `docs/writing-a-program.md` (new) for adding a domain authority.
- `docs/writing-a-routine.md` (rewritten) for adding a scheduled dispatcher.
- `docs/briefs/2026-04-18-v0.4-observability-brief.md`.

Changed:
- `routines/` now holds thin cron dispatchers (6 files, ~25-40 lines each). Each routine references a program and a named behavior, defines a target, run report, and worker discipline. Install, verify, and uninstall instructions live in their own top-level docs, not in the routine. Behavioral detail lives in the program it dispatches, not in the routine.
- `INSTALL_FOR_AGENTS.md` renamed to `INSTALL.md`.
- Six-routine catalog (four programs):
  - `daily-note` (always-on) -> `daily-notes` program, tend today's note.
  - `seal-past-days` (burst) -> `daily-notes` program, seal a past-day note.
  - `para-extract` (burst) -> `para` program, extract PARA from a sealed note.
  - `para-align` (fixed cron, Sunday 06:00 UTC) -> `para` program, align PARA structure.
  - `workspace-tidy` (always-on, every 2h) -> `workspace-tidy` program, walk and tidy.
  - `git-hygiene` (always-on, every 30m) -> `git-hygiene` program, commit drift.
- Every routine is now a cron job. Execution classes simplified to two: **Always-on cron** and **Heartbeat-toggled burst**. The `heartbeat-direct`, `heartbeat-inline`, and `ambient` classes are retired.
- Workspace install produces two symlinks: `clawstodian/programs` -> `~/clawstodian/programs` and `clawstodian/routines` -> `~/clawstodian/routines`.
- `templates/HEARTBEAT.md` (new) is the collaborative maintainer thread: reviews workspace state, toggles burst workers, spot-checks health, appends tick trace, and posts to the notifications channel. Includes a `tasks:` YAML block with three cadences (2h status sweep, daily retrospective, weekly review) so only due tasks fire each tick. Does not execute programs. Replaces the earlier `HEARTBEAT-SECTION.md` at the repo root - workspace HEARTBEAT.md is now treated as a regular installable template like MEMORY.md and the others.
- Recommended heartbeat gateway config: heartbeat runs in the agent's main session (defaults: no `session` override, `isolatedSession: false`, `lightContext: false`). Collaboration happens in the operator's DM with the agent; a dedicated notifications channel receives heartbeat status posts, retrospectives, reviews, and per-routine announcements as one pane of workspace-maintenance observability. Channel replies there do not route back to the main session - that's OpenClaw's routing behavior and is the correct read-mostly model for observability. Per-tick cost rises from ~5K (isolated) to ~20-50K tokens (main session, full bootstrap) in exchange for collaborative continuity and workspace awareness. clawstodian deliberately does NOT set `session.maintenance`, `agents.defaults.contextPruning`, `session.dmScope`, or `session.reset` - those are host-wide baseline choices the operator makes separately. No named maintainer session to create; no `sessions_send` bridge needed; no channel-to-session binding required. `docs/heartbeat-config.md` has the full rationale.
- `templates/AGENTS.md` (new) carries the workspace charter with two catalogs: four programs (primary, domain authorities) and six routines (scheduled invocations appendix). Replaces the earlier `AGENTS-SECTION.md`.
- Template markers renamed: `clawstodian/agents-section` -> `clawstodian/agents`, `clawstodian/heartbeat-section` -> `clawstodian/heartbeat`. The old names are still recognized by INSTALL/VERIFY/UNINSTALL for backward compatibility with workspaces installed before this rename.
- `templates/crons.md` lists all six routines with the program/behavior each invokes.
- Template markers bumped from `2026-04-17` to `2026-04-18`.

Removed (from the v0.3 set; their responsibilities moved):
- `programs/para-tend.md` - subsumed by the `para` program's extract behavior, invoked via the `para-extract` routine.
- `programs/durable-insight.md` - inline-capture folded into the `daily-notes` program's tend behavior; filing folded into the `para` program's extract behavior; unreliable ambient trigger dropped.
- `programs/health-sweep.md` - runtime observability is now a byproduct of the heartbeat orchestrator's executive summary.
- `daily-notes-tend`, `close-of-day`, `para-backfill`, `weekly-para-align`, `workspace-tidiness` names - replaced by the routine names above.

Motivating evidence: on 2026-04-18 morning, the wellgent install showed `heartbeat: started` at 22:48:50 UTC the previous night followed by zero tick events all day, while cron jobs (Dreaming promotion at 09:04 UTC) fired cleanly. Heartbeat passes every potential tick through roughly seven silent-skip gates (`areHeartbeatsEnabled`, per-agent enablement, `isWithinActiveHours`, lane queues, delivery resolution, visibility); any one can short-circuit without emitting. Cron has one observable delivery path per job. The structural lesson: put observable, resilient execution on cron; keep heartbeat light and never silent. The program/routine split then surfaced as the cleaner axis to reconcile "agents do this during sessions" with "cron catches what agents missed" without conflating behavior and scheduling.

## 0.3.0-draft - 2026-04-17

Catalog model. The v0.2 draft embedded full program specs inside `AGENTS-SECTION.md` and embedded per-interval task prompts inside `HEARTBEAT-SECTION.md`. v0.3 separates authority from spec: programs are cataloged in `AGENTS.md`, spec files live in `programs/`, and the heartbeat coordinator reads spec files fresh each tick.

Added:
- Six new heartbeat-program specs under `programs/`: `daily-notes-tend`, `durable-insight`, `para-tend`, `workspace-tidiness`, `git-hygiene`, `health-sweep`. Previously these were inline in `AGENTS-SECTION.md`.

Changed:
- Renamed `cron-routines/` to `programs/`. Cron routines and heartbeat programs now share one home.
- `AGENTS-SECTION.md` is now a catalog pointing at `clawstodian/programs/<name>.md`, not inline specs. Size dropped from ~15k to ~5k characters. Spec discipline: "read the spec before executing any program."
- `HEARTBEAT-SECTION.md` is a pure coordinator (prose dispatcher, no YAML `tasks:` block). Each tick reads workspace state fresh and decides which programs need attention. Shape matches what wellgent iterated to in practice.
- Workspace symlink convention simplified from N per-file symlinks to one `clawstodian/programs → ~/clawstodian/programs` directory symlink.
- Template markers bumped from `2026-04-16` to `2026-04-17` for changed sections.
- `README.md`, `INSTALL_FOR_AGENTS.md`, `templates/crons.md`, `docs/architecture.md`: updated for the rename and new shape.
- `INSTALL_FOR_AGENTS.md`: Step 5 uses a single directory symlink; Step 3 survey compares marker dates for update detection; new "Updating an existing install" section for re-runs.

Trade-off:
- The pure-coordinator heartbeat runs the LLM every tick (no OpenClaw `no-tasks-due` skip). Picked over the hybrid `tasks:` model because every tick has at least one thing to check (today's daily note) and the coordinator discipline is cleaner. Workspaces that want stricter interval control can replace `HEARTBEAT.md` with a `tasks:` block.

## 0.2.0-draft - 2026-04-16

Scope realignment. The v0.1 draft was too minimal to replace the ops-* packages. v0.2 reshapes the package around six explicit programs that cover all the ops-daily / ops-para / ops-clean goals through heartbeat-driven execution.

Added:
- Six program definitions in `AGENTS-SECTION.md` using the standing-orders anatomy (daily notes, durable insight capture, PARA graph, workspace tidiness, git hygiene, health sweep).
- `HEARTBEAT-SECTION.md` tasks block that runs and orchestrates the programs.
- `INSTALL_FOR_AGENTS.md` for agent-driven one-line install.
- `templates/para-structure.md`, `templates/daily-note-structure.md`, `templates/MEMORY.md`, `templates/crons.md` as installable workspace reference docs.
- `cron-routines/close-of-day.md` (demand-driven burst, heartbeat-managed) and `cron-routines/weekly-para-align.md` (plain weekly scheduled job) as opt-in cron routines. Each routine file holds the full run instructions (target selection, exec safety, trivial-day fast-path, what-to-do, after-processing, commit, failure handling, reply format) and the install command at the bottom. The cron's `--message` is a one-liner pointing back to the routine file, so routine updates take effect without editing cron state.
- Realignment brief at `docs/briefs/2026-04-16-realignment-brief.md`.

Changed:
- `README.md` rewritten to describe the program model and agent-driven install.
- `docs/architecture.md` updated for the heartbeat-as-orchestrator / cron-as-burst-worker pattern.
- `AGENTS.md` updated key files list.

Removed:
- `setup.sh` - superseded by agent-driven install in `INSTALL_FOR_AGENTS.md`.
- `SETUP.md` - folded into `README.md` and `INSTALL_FOR_AGENTS.md`.
- `templates/HEARTBEAT.md` - superseded by root-level `HEARTBEAT-SECTION.md`.

Absorbed into `AGENTS-SECTION.md` from the retiring ops-* packages' AGENTS sections:
- Memory and navigation orientation (three-layer model, finding-things workflow, convention deep-dive pointers).
- Memory maintenance rules (log in canonical daily note, one file per day, internalize-don't-collect, docs describe the present). These are universal workspace rules, not heartbeat-specific.
- Commit topic conventions in program 5 (`<topic>: <short description>` with a shared topic list).

When ops-* retires, a workspace can remove the `🧠 Memory`, `Pipeline (ops-para)`, `Daily Note Pipeline (ops-daily)`, and `Workspace Cleanup & Git Hygiene (ops-clean)` sections from its `AGENTS.md` without losing these universal conventions - they now live inside the clawstodian section.

## 0.1.0-draft - 2026-04-16

- Created the `clawstodian` project as a draft sharable package.
- Wrote the initial package README and architecture document.
- Drafted the first implementation brief.
- Added an initial workspace `AGENTS.md` section and `HEARTBEAT.md` template.
- Documented the intended setup flow and package boundaries.
