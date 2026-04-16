# clawstodian

A sharable OpenClaw agent package that turns a workspace into a heartbeat-driven maintainer. Daily notes, durable insight capture, PARA knowledge graph, workspace tidiness, git hygiene, and health monitoring - all handled by the main-session agent on a quiet cadence, with the workspace itself as the only ledger.

Successor to `ops-daily`, `ops-para`, and `ops-clean`. Same jobs, native OpenClaw primitives, far fewer moving parts.

## One-line install for an agent

Paste into a running OpenClaw or Claude Code session:

> Retrieve and follow the instructions at: `https://raw.githubusercontent.com/<org>/clawstodian/main/INSTALL_FOR_AGENTS.md`

The agent clones the package, surveys your workspace, proposes a merge plan, asks whatever it needs to ask, and applies on your approval. Nothing is overwritten silently.

## What it does

Six programs defined in `AGENTS-SECTION.md` and executed by the heartbeat tasks in `HEARTBEAT-SECTION.md`:

- **Daily notes.** One canonical `memory/YYYY-MM-DD.md` per day. Sourced from `sessions_*` tools, raw transcript JSONL for fidelity when sealing, `git log`, and workspace diffs.
- **Durable insight capture.** When something meaningful happened, file it. Batched signalling, co-created placement, no stubs.
- **PARA knowledge graph.** Projects, areas, resources, archives at workspace root per the established convention. Auto-create when placement is obvious; ask when ambiguous.
- **Workspace tidiness.** Empty dirs, orphans, stale run-logs, archive hygiene. Suggest before touching anything unfamiliar.
- **Git hygiene.** Commit meaningful drift, one concern per commit, never `git add -A`, no AI attribution. Consult before non-obvious `.gitignore` additions.
- **Health sweep.** Surface anomalies with likely causes and proposed resolutions. Never auto-repair configs.

## How it runs

- **Heartbeat** is the orchestrator. On a default 30-minute cadence, due tasks in `HEARTBEAT.md` run the programs. Each tick is isolated and light-context (roughly 2-5K tokens instead of 100K).
- **Cron** is optional. Two recipes ship: `close-of-day` (`every 30m` while enabled; heartbeat enables on demand when past-day notes accumulate; self-disables when queue empty) and `weekly-para-align` (simple `Sunday 06:00` verification pass).
- **No package state files.** Git, daily notes, PARA entities, and session transcripts are the ledger.

## Co-creation, not automation

The maintainer is a scribe, not an architect. Four rules it runs by:

1. When placement is obvious, just act.
2. When placement is ambiguous, ask in one short question.
3. Signal in batches: one "filed / committed / surfaced" summary per tick, not per action.
4. Surface problems with likely causes and one or two resolution paths. Do not just alert; collaborate.

## Manual install (for non-agent users)

```bash
git clone https://github.com/<org>/clawstodian.git ~/clawstodian
cd ~/clawstodian
less INSTALL_FOR_AGENTS.md
```

Follow the steps yourself, or paste the one-line install into a running agent and let it do the work.

## Repo shape

```
clawstodian/
  README.md                          this file
  INSTALL_FOR_AGENTS.md              agent-driven install entry point

  AGENTS-SECTION.md                  charter + six program definitions
  HEARTBEAT-SECTION.md               heartbeat tasks that run the programs

  templates/
    para-structure.md                installable to memory/para-structure.md
    daily-note-structure.md          installable to memory/daily-note-structure.md
    MEMORY.md                        installable to workspace root MEMORY.md
    crons.md                         installable to memory/crons.md

  cron-recipes/
    close-of-day.md                  past-day sealing burst (opt-in)
    weekly-para-align.md             weekly PARA integrity burst (opt-in)

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
        every: "30m",
        isolatedSession: true,
        lightContext: true,
        includeReasoning: false,
        target: "none",
        activeHours: {
          start: "08:00",
          end: "22:00",
          timezone: "UTC"
        }
      }
    }
  }
}
```

`isolatedSession` + `lightContext` are deliberate. Cross-tick memory lives in the workspace, not in session history. Every tick reads what it needs from files, acts, writes its observations back, and forgets.

## Status

Draft. See `VERSION` and `CHANGELOG.md`. The design is stable; install wiring and some program details are still firming up.

## License

MIT
