# Changelog

## 0.2.0-draft - 2026-04-16

Scope realignment. The v0.1 draft was too minimal to replace the ops-* packages. v0.2 reshapes the package around six explicit programs that cover all the ops-daily / ops-para / ops-clean goals through heartbeat-driven execution.

Added:
- Six program definitions in `AGENTS-SECTION.md` using the standing-orders anatomy (daily notes, durable insight capture, PARA graph, workspace tidiness, git hygiene, health sweep).
- `HEARTBEAT-SECTION.md` tasks block that runs and orchestrates the programs.
- `INSTALL_FOR_AGENTS.md` for agent-driven one-line install.
- `templates/para-structure.md`, `templates/daily-note-structure.md`, `templates/MEMORY.md`, `templates/crons.md` as installable workspace reference docs.
- `cron-recipes/close-of-day.md` (demand-driven burst, heartbeat-managed) and `cron-recipes/weekly-para-align.md` (plain weekly scheduled job) as opt-in cron recipes.
- Realignment brief at `docs/briefs/2026-04-16-realignment-brief.md`.

Changed:
- `README.md` rewritten to describe the program model and agent-driven install.
- `docs/architecture.md` updated for the heartbeat-as-orchestrator / cron-as-burst-worker pattern.
- `AGENTS.md` updated key files list.

Removed:
- `setup.sh` - superseded by agent-driven install in `INSTALL_FOR_AGENTS.md`.
- `SETUP.md` - folded into `README.md` and `INSTALL_FOR_AGENTS.md`.
- `templates/HEARTBEAT.md` - superseded by root-level `HEARTBEAT-SECTION.md`.

## 0.1.0-draft - 2026-04-16

- Created the `clawstodian` project as a draft sharable package.
- Wrote the initial package README and architecture document.
- Drafted the first implementation brief.
- Added an initial workspace `AGENTS.md` section and `HEARTBEAT.md` template.
- Documented the intended setup flow and package boundaries.
