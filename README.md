# clawstodian

A sharable OpenClaw agent package that turns a workspace into a cron-driven maintenance system with a lightweight heartbeat orchestrator. The package ships **four programs** (domain authorities for daily notes, PARA knowledge graph, workspace tidiness, git hygiene) and **six routines** (scheduled cron invocations of specific program behaviors) so the workspace stays in good shape whether the operator is actively working or not.

Successor to `ops-daily`, `ops-para`, and `ops-clean`. Same jobs, native OpenClaw primitives, and the observable-by-design execution pattern those packages got right.

## Programs and routines

**Programs** are the authorities for how the workspace is operated in a domain. Each program spec describes conventions, authority, approval gates, escalation rules, and the behaviors the agent can perform. Programs are read at session bootstrap via `AGENTS.md` so any agent in the workspace knows how the domain is governed. Routines (below) and agents in normal sessions both follow the same programs.

**Routines** are thin scheduled invocations. Each routine references a program, picks a specific behavior to run, defines a target and a run report, and registers a cron job. Routines are the catch-up safety net for what agents did not do in-session.

The split is **what** (programs) vs **when** (routines). Multiple routines can invoke the same program - for example, `capture-sessions` (burst, ingest session activity into daily notes) and `seal-past-days` (burst, seal a past-day note) both reference behaviors from the `daily-notes` program.

## Install into any workspace

```bash
git clone https://github.com/wellgent/clawstodian.git ~/clawstodian
```

Then tell your running OpenClaw or Claude Code agent:

> Install clawstodian into my workspace. Follow `INSTALL.md` in the clawstodian repo.

The agent reads `INSTALL.md`, surveys your workspace, proposes a merge plan, asks whatever it needs to ask, applies on your approval, and finishes with a smoke test. Nothing is overwritten silently.

## What it installs

**Four programs** (`programs/`): the domain authorities.

- `daily-notes` - canonical daily notes at `memory/YYYY-MM-DD.md`. Covers tending today's note and sealing past-day notes.
- `para` - the PARA knowledge graph (projects/areas/resources/archives). Covers extracting entities from sealed notes and aligning structural + semantic health.
- `workspace-tidy` - workspace cleanliness. Trash removal, misplaced-file relocation, `.gitignore` upkeep.
- `git-hygiene` - commit discipline. Stage-by-path commits, clear messages, immediate push.

**Six routines** (`routines/`): the scheduled invocations.

Always-on crons:
- `workspace-tidy` (every 2h) - workspace-tidy: walk and tidy.
- `git-hygiene` (every 30m) - git-hygiene: commit drift.

Fixed cron:
- `para-align` (Sunday 06:00 UTC) - para: align PARA structure. Heartbeat may also `--wake now` on mid-week drift.

Heartbeat-toggled bursts (start disabled; orchestrator enables on demand):
- `capture-sessions` - daily-notes: capture one session's unread JSONL into the appropriate daily notes. Prioritizes live operator sessions over historical drain. Backstop for the agents' in-session note writing, not the primary writer.
- `seal-past-days` - daily-notes: seal a past-day note.
- `para-extract` - para: extract PARA from a sealed note.

`AGENTS.md` holds the programs catalog; `HEARTBEAT.md` runs the orchestrator; `memory/crons.md` is the routine dashboard; `memory/session-ledger.md` is the authoritative per-session capture-cursor file. All specs are read on demand from the workspace symlinks.

## How it runs

- **Each routine runs as its own cron job.** Isolated session, light context, per-routine announcement to the logs channel. A quiet run returns `NO_REPLY` and stays silent.
- **Heartbeat is the orchestrator, not an executor.** On its cadence it reads workspace state, toggles burst workers based on queues (sealed-notes pending, past-day notes unsealed), spot-checks configuration health, appends a trace line to `memory/heartbeat-trace.md`, and posts a one-line executive summary. It never goes silent: even a healthy no-change tick posts.
- **Three-layer observability.** Per-routine run reports (detail on demand), heartbeat executive summary (ambient awareness), `memory/heartbeat-trace.md` (forensic record). Silence in any of the three is itself informative.
- **No package-owned state files.** Git, daily notes, PARA entities, session transcripts, `memory/session-ledger.md` (authoritative capture state for daily-notes), and `memory/heartbeat-trace.md` are the only state.
- **In-session agents and cron dispatch share the same programs.** An agent finishing a work session can follow the `git-hygiene` program to commit drift; the `git-hygiene` routine fires every 30m to catch anything missed. Both read the same program spec.

## Co-creation, not automation

The maintainer is a scribe, not an architect. Four rules:

1. When placement is obvious, just act.
2. When placement is ambiguous, surface (in-session: ask the user; via cron: include in run report).
3. Each routine announces its own run: one single-line report per cron firing.
4. Surface problems with likely causes and one or two resolution paths. Do not just alert; collaborate.

## Manual install (without an agent)

Clone to `~/clawstodian`, open `INSTALL.md`, and follow the steps yourself. Everything is explicit and reversible.

## Repo shape

```
clawstodian/
  README.md                          this file
  INSTALL.md                         agent-driven install entry point
  VERIFY.md                          standalone verification checks
  UNINSTALL.md                       full removal flow


  programs/
    daily-notes.md                   domain: canonical daily notes
    para.md                          domain: PARA knowledge graph
    workspace-tidy.md                domain: workspace cleanliness
    git-hygiene.md                   domain: commit discipline

  routines/
    workspace-tidy.md                always-on; invokes workspace-tidy/walk-and-tidy
    git-hygiene.md                   always-on; invokes git-hygiene/commit-drift
    para-align.md                    fixed cron; invokes para/align
    capture-sessions.md              burst; invokes daily-notes/capture
    seal-past-days.md                burst; invokes daily-notes/seal
    para-extract.md                  burst; invokes para/extract

  templates/
    AGENTS.md                        installable to workspace root AGENTS.md (workspace charter + catalogs)
    HEARTBEAT.md                     installable to workspace root HEARTBEAT.md (pure-orchestrator heartbeat)
    MEMORY.md                        installable to workspace root MEMORY.md
    para-structure.md                installable to memory/para-structure.md
    daily-note-structure.md          installable to memory/daily-note-structure.md
    crons.md                         installable to memory/crons.md
    session-ledger.md                installable to memory/session-ledger.md (daily-notes capture state)

  docs/
    architecture.md                  first-principles design
    heartbeat-config.md              heartbeat gateway config reference
    writing-a-program.md             guide for adding new programs (domain authorities)
    writing-a-routine.md             guide for adding new routines (scheduled invocations)
    briefs/
      2026-04-16-realignment-brief.md         v0.2 scope brief
      2026-04-18-v0.4-observability-brief.md  v0.4 scope brief

  AGENTS.md                          this repo's own agent instructions
  CLAUDE.md                          symlink to AGENTS.md
  VERSION
  CHANGELOG.md
```

## Recommended heartbeat config

Heartbeat runs in the agent's main session (where the operator already DMs with the agent). Mixed cadence via `tasks:` in `templates/HEARTBEAT.md` (2h status, daily retrospective, weekly review). Delivery goes to a **dedicated notifications channel** for observability - the same channel that cron routines announce into.

```json5
{
  agents: {
    defaults: {
      heartbeat: {
        every: "2h",
        // session, isolatedSession, lightContext all omitted -> defaults:
        //   session: main (collaborative continuity with the operator)
        //   isolatedSession: false
        //   lightContext: false (full workspace bootstrap each tick)
        target: "discord", // channel plugin name: discord | slack | telegram | whatsapp | ...
        to: "channel:<your-notifications-channel-id>", // channel-specific recipient
        activeHours: {
          start: "08:00",
          end: "22:00",
          timezone: "UTC"
        }
      }
    }
  },
  channels: {
    defaults: {
      heartbeat: {
        showAlerts: true,
        useIndicator: true
      }
    }
  }
}
```

Clean split of purpose:

- **Main session (operator's DM with the agent)** = collaboration. The heartbeat inherits the full DM history, so the agent naturally remembers past ticks and your replies. This is the maintenance thread.
- **Notifications channel** = observability. Heartbeat posts status/retrospective/review summaries here. Cron routines also post their completion lines here. One pane for all workspace-maintenance activity. Read-mostly; replies there don't route back to the main session.

clawstodian deliberately does NOT set `session.maintenance`, `agents.defaults.contextPruning`, `session.dmScope`, or `session.reset` - those are host-wide policy choices the operator makes at the sessions-baseline level. The heartbeat config layers on top without overriding.

`docs/heartbeat-config.md` is the authoritative reference: rationale, cost profile, `tasks:` semantics, and troubleshooting.

## Bootstrap sizing

OpenClaw injects `AGENTS.md` into the system prompt each turn. Provider ceilings vary (e.g. the OpenAI Codex responses endpoint silently 400s when `instructions` exceeds ~32 KiB). clawstodian's catalog model keeps `AGENTS.md` lean - program and routine specs live in `clawstodian/programs/` and `clawstodian/routines/` and are read on demand, not injected every turn.

If your workspace's `AGENTS.md` is pushing the per-file cap (`agents.defaults.bootstrapMaxChars`, default 12,000), the catalog model alone usually resolves it.

## Status

Draft. See `VERSION` and `CHANGELOG.md`. v0.4 introduces the program/routine split, the cron-per-routine execution model, and three-layer observability; v0.4 drafts land alongside workspace evolution before stabilizing.

## License

MIT
