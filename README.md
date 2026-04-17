# clawstodian

A sharable OpenClaw agent package that turns a workspace into a heartbeat-driven maintainer. Daily notes, durable insight capture, PARA knowledge graph, workspace tidiness, git hygiene, and health monitoring - all handled by the main-session agent on a quiet cadence, with the workspace itself as the only ledger.

Successor to `ops-daily`, `ops-para`, and `ops-clean`. Same jobs, native OpenClaw primitives, far fewer moving parts.

## Install into any workspace

```bash
git clone https://github.com/wellgent/clawstodian.git ~/clawstodian
```

Then tell your running OpenClaw or Claude Code agent:

> Install clawstodian into my workspace. Follow `INSTALL_FOR_AGENTS.md` in the clawstodian repo.

The agent reads `INSTALL_FOR_AGENTS.md`, surveys your workspace, proposes a merge plan, asks whatever it needs to ask, and applies on your approval. Nothing is overwritten silently.

## What it installs

Nine programs shipped as individual specs in `programs/`, categorized by how they run:

**Heartbeat-direct** (run by `HEARTBEAT.md` each tick)
- `daily-notes-tend` - keep today's canonical daily note current
- `para-tend` - propagate one sealed note into PARA per tick
- `workspace-tidiness` - prune trash, remove stale scratch
- `git-hygiene` - commit meaningful drift, maintain `.gitignore`
- `health-sweep` - surface anomalies, never auto-repair

**Heartbeat-inline** (folded into another program's tick)
- `durable-insight` - file obvious insights, surface ambiguous ones

**Burst workers** (cron-driven, drain one unit per run, heartbeat toggles enable/disable)
- `close-of-day` - seal one unsealed past-day daily note
- `para-backfill` - propagate one sealed note through PARA

**Fixed cron** (own schedule)
- `weekly-para-align` - weekly PARA structural verification

Each spec uses the same anatomy: authority, trigger, approval gate, escalation, execution steps, what NOT to do. `AGENTS.md` holds the catalog; `HEARTBEAT.md` coordinates each tick; individual specs are read on demand.

## How it runs

- **Heartbeat** is the orchestrator. On a default 2-hour cadence, the coordinator in `HEARTBEAT.md` decides which programs need attention this tick, reads their specs fresh from `clawstodian/programs/`, executes, verifies, and reports once.
- **Cron** handles bursts and fixed schedules. `close-of-day` and `para-backfill` start disabled and are enabled by heartbeat on demand when a queue exists; `weekly-para-align` runs Sunday 06:00.
- **No package-owned state files.** Git, daily notes, PARA entities, and session transcripts are the ledger.
- **Isolated heartbeat sessions.** Each tick runs in a fresh isolated session with no prior chat history. Workspace bootstrap (`AGENTS.md`, `MEMORY.md`, etc.) caches across ticks.

## Co-creation, not automation

The maintainer is a scribe, not an architect. Four rules:

1. When placement is obvious, just act.
2. When placement is ambiguous, ask in one short question.
3. Signal in batches: one "filed / committed / surfaced" summary per tick, not per action.
4. Surface problems with likely causes and one or two resolution paths. Do not just alert; collaborate.

## Manual install (without an agent)

Clone to `~/clawstodian`, open `INSTALL_FOR_AGENTS.md`, and follow the steps yourself. Everything is explicit and reversible.

## Repo shape

```
clawstodian/
  README.md                          this file
  INSTALL_FOR_AGENTS.md              agent-driven install entry point

  AGENTS-SECTION.md                  workspace charter + catalog of programs
  HEARTBEAT-SECTION.md               pure-coordinator heartbeat dispatcher

  programs/
    daily-notes-tend.md              heartbeat-direct
    durable-insight.md               heartbeat-inline
    para-tend.md                     heartbeat-direct
    workspace-tidiness.md            heartbeat-direct
    git-hygiene.md                   heartbeat-direct
    health-sweep.md                  heartbeat-direct
    close-of-day.md                  burst worker
    para-backfill.md                 burst worker
    weekly-para-align.md             fixed cron

  templates/
    para-structure.md                installable to memory/para-structure.md
    daily-note-structure.md          installable to memory/daily-note-structure.md
    MEMORY.md                        installable to workspace root MEMORY.md
    crons.md                         installable to memory/crons.md

  docs/
    architecture.md                  first-principles design
    briefs/
      2026-04-16-realignment-brief.md        v0.2 scope brief

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
        includeReasoning: false,
        target: "<your-maintainer-channel-id>",  // recommended: explicit channel ID; fallback: "last"
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
        showOk: false,      // suppress HEARTBEAT_OK acks
        showAlerts: true,   // deliver real tick summaries
        useIndicator: true  // emit UI indicator events
      }
    }
  }
}
```

`isolatedSession: true` is deliberate: cross-tick memory lives in the workspace, not in session history. Every tick reads what it needs from files, acts, writes observations back, and forgets.

**Recommended:** set `target` to a dedicated channel ID (Telegram chat ID, Slack channel ID, Discord channel ID) so maintainer updates land in one predictable place.

## Bootstrap sizing

OpenClaw injects `AGENTS.md` into the system prompt each turn. Provider ceilings vary (e.g. the OpenAI Codex responses endpoint silently 400s when `instructions` exceeds ~32 KiB). clawstodian's catalog model keeps `AGENTS.md` lean - program specs live in `clawstodian/programs/` and are read on demand, not injected every turn.

If your workspace's AGENTS.md is pushing the per-file cap (`agents.defaults.bootstrapMaxChars`, default 12,000), the catalog model alone usually resolves it. If not, extract domain-specific sections into project READMEs or resource docs and leave pointers behind.

## Status

Draft. See `VERSION` and `CHANGELOG.md`. The design is stable; install wiring and some program details are still firming up.

## License

MIT
