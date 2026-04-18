# clawstodian

A sharable OpenClaw agent package that turns a workspace into a cron-driven maintenance system with a lightweight heartbeat orchestrator. Daily notes, PARA knowledge graph, workspace tidiness, and git hygiene - all handled by six focused routines that each run on their own cron, each announcing their own completion to the operator's logs channel.

Successor to `ops-daily`, `ops-para`, and `ops-clean`. Same jobs, native OpenClaw primitives, and the observable-by-design execution pattern those packages got right.

## Install into any workspace

```bash
git clone https://github.com/wellgent/clawstodian.git ~/clawstodian
```

Then tell your running OpenClaw or Claude Code agent:

> Install clawstodian into my workspace. Follow `INSTALL_FOR_AGENTS.md` in the clawstodian repo.

The agent reads `INSTALL_FOR_AGENTS.md`, surveys your workspace, proposes a merge plan, asks whatever it needs to ask, applies on your approval, and finishes with a smoke test. Nothing is overwritten silently.

## What it installs

Six routines under `routines/`, each its own cron job:

**Always-on crons**
- `daily-note` - keep today's canonical note current; merge slug siblings; file obvious durable insights
- `workspace-tidy` - remove trash, move misplaced files to intuitive homes
- `git-hygiene` - commit meaningful drift, maintain `.gitignore`
- `para-align` - weekly PARA structural and semantic health (cross-references, naming, MEMORY.md currency)

**Heartbeat-toggled bursts** (start disabled; orchestrator enables on demand)
- `seal-past-days` - seal one unsealed past-day daily note per run
- `para-extract` - propagate one sealed note into PARA entities per run

Each spec follows the same anatomy: authority, trigger, approval gates, escalation, execution steps, reply format, install, verify. `AGENTS.md` holds the catalog; `HEARTBEAT.md` runs the orchestrator; individual specs are read on demand.

## How it runs

- **Every routine runs as its own cron job.** Isolated session, light context, per-routine announcement to the logs channel. A quiet run replies `NO_REPLY` and stays silent.
- **Heartbeat is the orchestrator, not an executor.** On its cadence it reads workspace state, toggles burst workers based on queues (sealed-notes pending, past-day notes unsealed), spot-checks configuration health, appends a trace line to `memory/heartbeat-trace.md`, and posts a one-line executive summary to the logs channel. It never goes silent: even a healthy no-change tick posts.
- **Three-layer observability.** Per-routine announcements (detail on demand), heartbeat executive summary (ambient awareness), `memory/heartbeat-trace.md` (forensic record). If any of the three goes silent, that silence is itself informative.
- **No package-owned state files.** Git, daily notes, PARA entities, session transcripts, and `memory/heartbeat-trace.md` are the ledger.
- **Isolated sessions for every routine and every heartbeat tick.** Cross-tick memory lives in the workspace, not in session history.

## Co-creation, not automation

The maintainer is a scribe, not an architect. Four rules:

1. When placement is obvious, just act.
2. When placement is ambiguous, surface it in the routine's reply and wait.
3. Announce per routine: each cron posts its own single-line summary.
4. Surface problems with likely causes and one or two resolution paths. Do not just alert; collaborate.

## Manual install (without an agent)

Clone to `~/clawstodian`, open `INSTALL_FOR_AGENTS.md`, and follow the steps yourself. Everything is explicit and reversible.

## Repo shape

```
clawstodian/
  README.md                          this file
  INSTALL_FOR_AGENTS.md              agent-driven install entry point

  AGENTS-SECTION.md                  workspace charter + catalog of routines
  HEARTBEAT-SECTION.md               pure-orchestrator heartbeat

  routines/
    daily-note.md                    always-on cron
    workspace-tidy.md                always-on cron
    git-hygiene.md                   always-on cron
    para-align.md                    fixed cron (weekly) + heartbeat-wakeable
    seal-past-days.md                heartbeat-toggled burst
    para-extract.md                  heartbeat-toggled burst

  templates/
    para-structure.md                installable to memory/para-structure.md
    daily-note-structure.md          installable to memory/daily-note-structure.md
    MEMORY.md                        installable to workspace root MEMORY.md
    crons.md                         installable to memory/crons.md

  docs/
    architecture.md                  first-principles design
    writing-a-routine.md             guide for adding new routines
    briefs/
      2026-04-16-realignment-brief.md        v0.2 scope brief
      2026-04-18-v0.4-observability-brief.md v0.4 scope brief

  AGENTS.md                          this repo's own agent instructions
  CLAUDE.md                          symlink to AGENTS.md
  VERSION
  CHANGELOG.md
```

## Recommended heartbeat config

```json5
{
  agents: {
    defaults: {
      heartbeat: {
        every: "2h",
        isolatedSession: true,
        lightContext: true,
        includeReasoning: false,
        target: "<your-maintainer-channel-id>",
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

`isolatedSession: true` and `lightContext: true` together keep per-tick cost low while the orchestrator does its observational work. Every tick posts a summary (the orchestrator never replies with `HEARTBEAT_OK` alone), so `showOk` is irrelevant in v0.4.

**Recommended:** set `target` to a dedicated channel ID (Telegram chat ID, Slack channel ID, Discord channel ID) so maintainer updates land in one predictable place. The same channel receives per-routine announcements, keeping the operational thread in one place.

## Bootstrap sizing

OpenClaw injects `AGENTS.md` into the system prompt each turn. Provider ceilings vary (e.g. the OpenAI Codex responses endpoint silently 400s when `instructions` exceeds ~32 KiB). clawstodian's catalog model keeps `AGENTS.md` lean - routine specs live in `clawstodian/routines/` and are read on demand by the cron runner, not injected every turn.

If your workspace's `AGENTS.md` is pushing the per-file cap (`agents.defaults.bootstrapMaxChars`, default 12,000), the catalog model alone usually resolves it.

## Status

Draft. See `VERSION` and `CHANGELOG.md`. v0.4 introduces the cron-per-routine model and three-layer observability; v0.4 drafts land alongside workspace evolution before stabilizing.

## License

MIT
