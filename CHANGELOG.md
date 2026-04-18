# Changelog

## 0.4.0-draft - 2026-04-18

Cron-per-routine inversion and three-layer observability. v0.3 kept the heartbeat executing five routines in a pure-prose dispatcher; in live use a gateway restart produced a silent heartbeat failure with no detectable signal. v0.4 pushes routine execution onto cron (the self-observing substrate) and shrinks the heartbeat to a pure orchestrator that never goes silent.

Added:
- `memory/heartbeat-trace.md` append-only tick log as the forensic record that proves heartbeat fired.
- Executive summary to logs channel on every heartbeat tick (including healthy no-change ticks).
- Per-routine announcements to the logs channel via `--announce --channel --to` on every cron.
- Install smoke test in `INSTALL_FOR_AGENTS.md` that verifies markers, symlinks, templates, and cron registrations in under ten seconds.
- `para_status` field documented in `templates/daily-note-structure.md` as the PARA extraction queue marker (`pending -> done`).
- `docs/briefs/2026-04-18-v0.4-observability-brief.md`.

Changed:
- Directory renamed: `programs/` -> `routines/`. Symlink target updated to `clawstodian/routines`.
- Six-routine catalog (down from nine):
  - `daily-notes-tend` folded into `daily-note`.
  - `close-of-day` renamed `seal-past-days`.
  - `para-backfill` renamed `para-extract` and consolidated with PARA responsibilities from `para-tend` and `durable-insight`.
  - `workspace-tidiness` renamed `workspace-tidy`, scope expanded to active filing.
  - `weekly-para-align` renamed `para-align`, scope expanded (cross-references, naming conventions, MEMORY.md currency).
  - `git-hygiene` retained, unchanged in function.
- Every routine is now a cron job. Execution classes simplified to two: **Always-on cron** and **Heartbeat-toggled burst**. The `heartbeat-direct`, `heartbeat-inline`, and `ambient` classes are retired.
- `HEARTBEAT-SECTION.md` is now a pure orchestrator: reads state, toggles burst workers, spot-checks health, appends tick trace, posts executive summary. Does not execute routines.
- `AGENTS-SECTION.md` catalog reflects the six-routine shape and two execution classes.
- `templates/crons.md` reflects all six routines with schedules and enable logic.
- `docs/writing-a-program.md` renamed `docs/writing-a-routine.md` and rewritten for v0.4 model.
- Template markers bumped from `2026-04-17` to `2026-04-18`.

Removed:
- `programs/para-tend.md` - subsumed by `para-extract`.
- `programs/durable-insight.md` - inline-capture folded into `daily-note`; PARA filing folded into `para-extract`; unreliable ambient trigger dropped.
- `programs/health-sweep.md` - runtime observability is now a byproduct of the heartbeat orchestrator's executive summary.

Motivating evidence: on 2026-04-18 morning, the wellgent install showed `heartbeat: started` at 22:48:50 UTC the previous night followed by zero tick events all day, while cron jobs (Dreaming promotion at 09:04 UTC) fired cleanly. Heartbeat passes every potential tick through roughly seven silent-skip gates (`areHeartbeatsEnabled`, per-agent enablement, `isWithinActiveHours`, lane queues, delivery resolution, visibility); any one can short-circuit without emitting. Cron has one observable delivery path per job. The structural lesson: put observable, resilient execution on cron; keep heartbeat light and never silent.

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
