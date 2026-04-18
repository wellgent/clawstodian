# Changelog

## 0.4.0-draft - 2026-04-18

Program/routine split, cron-per-routine inversion, three-layer observability. v0.3 kept the heartbeat executing five routines in a pure-prose dispatcher; in live use a gateway restart produced a silent heartbeat failure with no detectable signal. v0.4 separates domain authorities (programs) from scheduled invocations (routines), pushes execution onto cron (the self-observing substrate), and shrinks the heartbeat to a pure orchestrator that never goes silent.

The v0.4 draft went through several iterations inside the `2026-04-18` day. The first pass merged behavior and scheduling into a single set of "routines." The second pass separated them: behavior lives in `programs/` (domain authorities), scheduling lives in `routines/` (thin cron dispatchers). The third pass stripped install/verify/uninstall sections out of routine specs and extracted them into top-level `INSTALL.md`, `VERIFY.md`, and `UNINSTALL.md` so routines stay purely behavioral. The fourth pass reshaped the heartbeat from the prior isolated, pure-orchestrator model to a collaborative-maintainer model: heartbeat runs in the agent's main session (where the operator already collaborates with the agent by DM) and posts to a dedicated notifications channel for observability. Mixed cadence via a `tasks:` block in `templates/HEARTBEAT.md` (2h status, daily retrospective, weekly review). The fifth pass hardened the daily-notes capture mechanism: introduced `memory/session-ledger.md` as the workspace-owned authoritative capture-cursor file, split session capture into a steady-state arm (`daily-note` over a 6h activeMinutes window) and a historical arm (`backfill-sessions` burst worker), formalized a classification step so `cron` / `hook` / subagent / delivery-only sessions are filtered before content flows, added `tools.sessions.visibility: "all"` as a required config prerequisite so isolated cron sessions can actually observe other sessions' transcripts, wired in a 2h midnight grace on seal-past-days target selection to prevent a race with midnight-straddling session capture, and added stale-cursor detection + bleed aggregation to the heartbeat orchestrator. The sixth pass consolidated `daily-note` (always-on every 30m) + `backfill-sessions` (burst) into a single `capture-sessions` routine (heartbeat-toggled burst): the two routines performed the same cursor-advance operation on the same ledger and differed only in their session selector, so unifying them collapses 48 no-op firings per day into zero on quiet workspaces, reflects the actual relationship between in-session agent writes (primary) and cron capture (backstop), and lets the cron prioritize live operator sessions over historical drain within a single queue sorted by `updatedAt`. The final shape is what this entry describes.

Added:
- `programs/` directory with four domain authorities: `daily-notes.md`, `para.md`, `workspace-tidy.md`, `git-hygiene.md`. Each is a thick spec describing conventions, authority, approval gates, escalation, and named behaviors. Programs are read at session bootstrap via `AGENTS.md` so any agent in the workspace follows the same domain rules whether invoked in-session or via cron.
- `docs/heartbeat-config.md` (new) - authoritative reference for the heartbeat gateway config: session model trade-offs, field-by-field rationale, `tasks:` interaction, channel binding for bidirectional flow, cost profile, troubleshooting.
- `memory/heartbeat-trace.md` append-only tick log as the forensic record that proves heartbeat fired.
- Executive summary to logs channel on every heartbeat tick (including healthy no-change ticks).
- Per-routine announcements to the logs channel via `--announce --channel --to` on every cron.
- `VERIFY.md` standalone verification doc: markers, both symlinks, programs + routines reachable, templates, cron registrations, heartbeat config sanity, visibility config, trace file, session ledger. Idempotent; can be run after install or any time. `INSTALL.md` references it as its final step.
- `UNINSTALL.md` standalone removal doc: disable and remove crons, remove symlinks, strip sections, revert heartbeat config, what to leave alone (including the session ledger).
- `para_status` field documented in `templates/daily-note-structure.md` as the PARA extraction queue marker (`pending -> done`).
- `templates/session-ledger.md` (new) - workspace-owned capture-state file for the daily-notes program. One H2 per session, cursor fields advanced in place via narrow `Edit` calls. Replaces ops-daily's `capture-state.json` sidecar. Semantics: session id heading + classification (interactive / skipped) + kind + first_seen + last_activity + lines_captured (JSONL line cursor) + dates_touched + status (active / dormant / done).
- `routines/capture-sessions.md` (new) - heartbeat-toggled burst that processes one session's unread JSONL per firing, covering both new-session admission and stale-cursor advance in a single routine. Picks the session with the newest `updatedAt` among those with gaps so live operator sessions capture first and historical drain runs in the background. Replaces the earlier split between `daily-note` (always-on) and `backfill-sessions` (burst) from earlier v0.4 drafts.
- `programs/daily-notes.md` capture step documents three reading layers for the unread JSONL span: `sessions_history` for small recent windows, inline `jq` filter piped to `/tmp/` for larger spans (empirically 100-200x reduction over raw Read), ad-hoc Python script in `/tmp/` for logic that does not fit one jq pipe. All three honor the exec-safety ban on heredoc-to-interpreter inlining. Motivated by measuring real session sizes: 15 of 383 sessions exceed 1 MB, one session is 16 MB and 88% of its bytes are tool results / tool calls the daily note does not want.
- Exec-safety blocks in every routine expanded to three concrete bullets: run commands by exact path (no eval/bash-c indirection), write multi-line script logic to `/tmp/clawstodian-<routine>-<context>.py` and invoke by path, one-line jq / `python3 -c` one-liners are allowed. Writing-a-routine guide updated with the same guidance.
- Session ledger format spec moved out of `templates/session-ledger.md` and into `docs/session-ledger.md`. The template is now an empty skeleton (marker + title + pointer to the doc); the doc carries the semantics, file shape, field definitions, update rules, and design rationale. `templates/` are workspace-installed files; `docs/` are the package's authoritative references. `daily-note-structure.md` and `para-structure.md` remain in `templates/` because they are workspace conventions the operator can customize; the session ledger is internal capture state and its format belongs with the package, not the workspace.
- `capture-sessions` routine: two-phase processing per firing. Phase 1 admits all un-admitted sessions unconditionally (classification is cheap - `kind` check plus user-message count). Phase 2 processes interactive gaps newest-first, bounded by token budget (~80 KB JSONL read across all sessions in one firing) and session count (hard cap 5). Replaces the earlier "one session per firing" rule, which created a net-negative pump on workspaces whose own cron activity generated as many new `skipped` sessions per day as single-session admissions could drain. Run report aggregates across all work done in the firing: `admitted <N> (skipped=<s>, interactive=<i>) | captured <M> sessions | dates [...] | merged <X> slugs | filed <Y> insights | bleed <Z> sealed | queue: un-admitted=<u>/stale=<s2>`.
- `programs/daily-notes.md` "Capture one session's new content" behavior is now a unit-of-work spec, not a per-firing spec. The program describes what happens for ONE session; the routine decides how many sessions per firing. Seal and para-extract behaviors remain strictly one-per-firing (they are heavier operations with no small-unit batching benefit); capture-sessions is the only routine that batches.
- `templates/HEARTBEAT.md` `tasks:` block decomposed from three tasks to four. `status` (2h) keeps only the per-tick minimum: gap accounting for capture/seal/extract, burst toggling, trace append, channel summary. `health` (24h, new) gets the heavier spot-checks: heartbeat config drift, `tools.sessions.visibility`, template markers, symlink resolution, cron registration presence, stalled-routine detection, long-running burst detection. `daily-retrospective` (24h) and `weekly-review` (168h) unchanged. Prose sections renamed `## Status task`, `## Health task`, etc. to mirror `tasks[].name`. When multiple tasks fire in the same tick (daily: status+health+retro; weekly: all four), the agent produces ONE combined channel post with sections delineated, not multiple messages.
- Program / routine responsibility split tightened. `programs/daily-notes.md` reduced to conventions only (goal, lifecycle, authority, approval gates, escalation, what-NOT-to-do); the 12-step session-capture procedure, the session-classification rules, the turn-level filtering rules, and the JSONL reading-layer guidance all moved into `routines/capture-sessions.md` where they actually apply. The seal target-selection, trivial-day fast-path, and full-seal editorial steps moved from the program into `routines/seal-past-days.md`. Programs now stay short (goal + conventions + gates) so in-session agents can absorb them at bootstrap without wading through cron-specific operational detail; routines carry the full procedure they execute on each firing.
- Session-ledger format spec moved from `docs/session-ledger.md` into `templates/daily-note-structure.md` as a new "Session Ledger" section. `docs/session-ledger.md` deleted. The ledger format is a workspace convention tightly coupled to the daily-notes pipeline and belongs alongside the daily-note format, not in a separate package doc.
- `programs/daily-notes.md` no longer lists prerequisites (`tools.sessions.visibility`, transcript-access tools). Those live in `INSTALL.md` where they actually get set up. The program's approval-gate for bleed-over now explicitly names the surfacing channels (in-session: ask the operator; under cron: include in run report), resolving an ambiguity a reader flagged.
- Run-report on disk: every routine firing that does meaningful work writes `memory/runs/<routine>/<YYYY-MM-DD>T<HH-MM-SS>Z.md` with structured detail (per-phase / per-action sections, counts, commit hashes, bleed lists, etc.). The channel summary remains a single scannable pipe-separated line and always ends with `report: memory/runs/<routine>/<ts>.md` so the operator has a one-step drill-down. NO_REPLY firings produce no file and no channel post. Applies to all six routines uniformly. `workspace-tidy` prunes run-report files older than 30 days (the per-routine directories themselves persist). Architecture and writing-a-routine docs updated. Token budget in `capture-sessions` raised from ~80K to ~140K (typical cron session window is ~200K with compaction at 160-180K; earlier number left too much headroom). JSONL per-firing cumulative cap raised from ~80 KB to ~500 KB (one large filtered session can itself reach 90 KB).
- `docs/writing-a-program.md` (new) for adding a domain authority.
- `docs/writing-a-routine.md` (rewritten) for adding a scheduled dispatcher.
- `docs/briefs/2026-04-18-v0.4-observability-brief.md`.

Changed:
- `routines/` now holds thin cron dispatchers (6 files, ~25-40 lines each). Each routine references a program and a named behavior, defines a target, run report, and worker discipline. Install, verify, and uninstall instructions live in their own top-level docs, not in the routine. Behavioral detail lives in the program it dispatches, not in the routine.
- `INSTALL_FOR_AGENTS.md` renamed to `INSTALL.md`.
- Six-routine catalog (four programs):
  - `capture-sessions` (burst) -> `daily-notes` program, capture one session's new content.
  - `seal-past-days` (burst) -> `daily-notes` program, seal a past-day note.
  - `para-extract` (burst) -> `para` program, extract PARA from a sealed note.
  - `para-align` (fixed cron, Sunday 06:00 UTC) -> `para` program, align PARA structure.
  - `workspace-tidy` (always-on, every 2h) -> `workspace-tidy` program, walk and tidy.
  - `git-hygiene` (always-on, every 30m) -> `git-hygiene` program, commit drift.
- Every routine is now a cron job. Execution classes: **Always-on cron**, **Fixed cron**, **Heartbeat-toggled burst**. The `heartbeat-direct`, `heartbeat-inline`, and `ambient` classes are retired.
- Workspace install produces two symlinks: `clawstodian/programs` -> `~/clawstodian/programs` and `clawstodian/routines` -> `~/clawstodian/routines`.
- `templates/HEARTBEAT.md` (new) is the collaborative maintainer thread: reviews workspace state, toggles burst workers, spot-checks health, appends tick trace, and posts to the notifications channel. Includes a `tasks:` YAML block with three cadences (2h status sweep, daily retrospective, weekly review) so only due tasks fire each tick. Does not execute programs. Replaces the earlier `HEARTBEAT-SECTION.md` at the repo root - workspace HEARTBEAT.md is now treated as a regular installable template like MEMORY.md and the others.
- Recommended heartbeat gateway config: heartbeat runs in the agent's main session (defaults: no `session` override, `isolatedSession: false`, `lightContext: false`). Collaboration happens in the operator's DM with the agent; a dedicated notifications channel receives heartbeat status posts, retrospectives, reviews, and per-routine announcements as one pane of workspace-maintenance observability. Channel replies there do not route back to the main session - that's OpenClaw's routing behavior and is the correct read-mostly model for observability. Per-tick cost rises from ~5K (isolated) to ~20-50K tokens (main session, full bootstrap) in exchange for collaborative continuity and workspace awareness. clawstodian deliberately does NOT set `session.maintenance`, `agents.defaults.contextPruning`, `session.dmScope`, or `session.reset` - those are host-wide baseline choices the operator makes separately. No named maintainer session to create; no `sessions_send` bridge needed; no channel-to-session binding required. `docs/heartbeat-config.md` has the full rationale.
- `templates/AGENTS.md` (new) carries the workspace charter with two catalogs: four programs (primary, domain authorities) and six routines (scheduled invocations appendix). Replaces the earlier `AGENTS-SECTION.md`.
- Template markers renamed: `clawstodian/agents-section` -> `clawstodian/agents`, `clawstodian/heartbeat-section` -> `clawstodian/heartbeat`. The old names are still recognized by INSTALL/VERIFY/UNINSTALL for backward compatibility with workspaces installed before this rename.
- `templates/crons.md` lists all six routines with the program/behavior each invokes.
- `programs/daily-notes.md` rewritten around the session-ledger cursor model: explicit prerequisites (`tools.sessions.visibility: "all"`), classification-before-tracking (cron / hook / subagent / delivery-only sessions filtered and recorded as `skipped`), per-session line-count cursor, sparse date detection from JSONL timestamps, past-date bleed-over surfacing for sealed notes. Two behaviors: "Capture one session's new content" (unified session capture, dispatched by `capture-sessions`) and "Seal a past-day note" (dispatched by `seal-past-days`). The primary writer of daily notes is the agent working in session with the operator per AGENTS.md memory rules; `capture-sessions` is the backstop that catches what the agent missed.
- `routines/capture-sessions.md` unifies the session-capture role: heartbeat-toggled burst with one session per firing, prioritized by newest `updatedAt` so live operator sessions capture before historical drain. Run report includes per-session counters (`lines from->to`, `dates`, `merged slugs`, `filed insights`, `bleed sealed`, `queue un-admitted/stale`).
- `templates/HEARTBEAT.md` status sweep extended: combined gap detection toggles `capture-sessions`; session-visibility drift surfaces as a health anomaly; tick trace line gains a `capture=<0|1>` field; channel summary reports `queues: capture=<u>+<s>/seal=<n>/extract=<m>` with un-admitted and stale-cursor subcounts.
- `templates/AGENTS.md` catalog now lists six routines and names `memory/session-ledger.md` as workspace state. Memory-maintenance rules explicitly frame agents as the primary writers of daily notes and `capture-sessions` as the backstop.
- `templates/daily-note-structure.md` clarifies that the `sessions:` frontmatter field is attribution only; capture cursors live in the ledger, not in daily-note frontmatter.
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
