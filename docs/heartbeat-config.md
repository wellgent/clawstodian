# Heartbeat configuration

This is the authoritative reference for configuring clawstodian's heartbeat. The heartbeat is an OpenClaw primitive; clawstodian ships a specific recommended configuration that supports the collaborative-maintainer model: one persistent session, mixed cadence via `tasks:`, and a dedicated channel the operator can read (and, with a small extra setup, write into).

The package's `templates/HEARTBEAT.md` is the workspace-level file the heartbeat reads on each tick. This doc is about the gateway-level config that wires that file into OpenClaw.

## What clawstodian uses the heartbeat for

The heartbeat is the agent's collaborative maintenance thread. On each tick, the agent:

- Reads workspace state (daily notes, `git status`, cron list, recent cron replies).
- Toggles burst workers based on queue presence.
- Posts a brief status line to the maintainer channel.
- On longer cadences: produces daily retrospectives and weekly reviews.

The operator reads these posts and can reply - those replies become part of the same conversation the heartbeat sees next tick.

The heartbeat does NOT execute program behaviors. Each routine runs as its own cron job (see `INSTALL.md` "Cron install commands"). The heartbeat is an observer, toggler, and collaborator.

## Session model: why persistent

The heartbeat can run in three session models:

- **Isolated** (`isolatedSession: true`) - fresh session every tick, no conversation history. Cheap (~2-5K tokens per tick). The agent reconstructs context from files; it cannot remember past ticks' conversations with the operator.
- **Main DM** (default, no isolation, no named session) - inherits the agent's main conversation. Continuity is automatic, but heartbeat directives and general operator chat share one context and pollute each other.
- **Named persistent** (`session: "session:<name>"`) - a dedicated session reused across ticks. Continuity preserved, clean separation from the main DM. This is what clawstodian uses.

The persistent maintainer session is the architecturally-right fit for "agent as collaborative maintainer." The operator sees a running thread of maintenance conversation, distinct from their ad-hoc chat with the same agent. The agent remembers what it flagged last tick, what the operator replied to, what is still in flight.

Cost is ~25-50K tokens per tick with `lightContext: true` (depends on session history length). Periodic auto-compaction bounds the growth.

## Recommended gateway config

```json5
{
  agents: {
    defaults: {
      heartbeat: {
        every: "2h",
        session: "session:clawstodian-maintainer",
        isolatedSession: false,
        lightContext: true,
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
  },
  session: {
    maintenance: {
      mode: "enforce",
      pruneAfter: "30d",
      maxEntries: 300
    }
  }
}
```

### Field rationale

- **`every: "2h"`** - matches the `status` task's cadence in `templates/HEARTBEAT.md`. A tighter cadence (e.g. `30m`) wastes budget; looser (`4h`) lets queues grow longer before the agent reacts. Adjust if your workspace has different tempo.
- **`session: "session:clawstodian-maintainer"`** - dedicated persistent session. Named explicitly so the operator can inspect and prune it later. Create it once at install time (see below).
- **`isolatedSession: false`** - opt out of isolation so conversation history persists. If you previously had `true`, flip to `false` and the session starts accumulating history from the next tick.
- **`lightContext: true`** - skips full workspace bootstrap except `HEARTBEAT.md`. Program and routine specs and PARA reference docs are not auto-loaded; the agent reads them explicitly when needed via `clawstodian/programs/<name>.md` and `clawstodian/routines/<name>.md` paths.
- **`target`** - the maintainer logs channel id. Use an explicit channel (Discord/Slack/Telegram) the operator actively watches. Avoid `"last"` and `"none"` for the maintainer use case.
- **`activeHours`** - the agent's working window. Outside this window ticks skip silently. Match the operator's actual availability.
- **`showAlerts: true`** - deliver substantive replies.
- **`useIndicator: true`** - emit UI indicator events so compact status renders work.
- **`session.maintenance`** - enforces compaction on long-lived sessions so the maintainer session doesn't grow unbounded. `maxEntries: 300` keeps roughly 25 days of 2h ticks before the oldest entries compact.

### Why `showOk` is not set

By default `showOk: false`, which suppresses `HEARTBEAT_OK` acks. In clawstodian's v0.4 model the agent is prompted to always produce a substantive (possibly one-line) reply on every tick - it never returns bare `HEARTBEAT_OK` - so the flag's value does not matter in practice. Setting it explicitly is optional.

## Create the maintainer session

The named session must exist before the heartbeat first targets it. One-time command:

```bash
openclaw sessions new session:clawstodian-maintainer
```

Or, if your OpenClaw build auto-creates named sessions on first use, the first heartbeat tick will create it. Check your OpenClaw version's `sessions` subcommand for the exact creation flow.

Verify:

```bash
openclaw sessions --json | grep clawstodian-maintainer
```

## How `tasks:` interacts with the config

`templates/HEARTBEAT.md` ships with a `tasks:` YAML block containing three tasks: `status` (2h), `daily-retrospective` (24h), `weekly-review` (168h / weekly). Each tick:

1. The gateway parses the `tasks:` block.
2. For each task, it checks if `now >= lastRun + interval` using per-task state stored in the session entry's `heartbeatTaskState`.
3. Only due tasks are included in the batched prompt sent to the model.
4. If zero tasks are due, the tick is skipped with `reason=no-tasks-due`. (This should not happen in steady state - the 2h status task matches the 2h heartbeat interval, so the status task fires every tick.)

Task last-run timestamps survive across ticks in session state regardless of session model, so switching between isolated and persistent sessions does not reset task cadence.

The prose content in `HEARTBEAT.md` below the `tasks:` block is appended as "Additional context" on every tick. That's where the detailed instructions for each task live, plus framing for the agent's role.

## Bidirectional flow: how the operator collaborates

The maintainer channel is where heartbeat posts land. For the operator to send messages back INTO the heartbeat's session so the next tick sees them, there are two paths:

### Path 1: `sessions_send` from the main DM agent

The operator DMs the agent normally. The agent uses the `sessions_send` tool to push a message into `session:clawstodian-maintainer`. The next heartbeat tick sees that message in its session context.

This works out of the box with no extra configuration. The main-session agent acts as a bridge.

Example operator prompt in DM: *"Tell the maintainer that the para-extract queue has been stuck at 3 for two days. Ask it to look into why."*

The main agent then calls `sessions_send` with the right session key.

### Path 2: Explicit channel-to-session binding

Some OpenClaw deployments support binding a specific channel to a specific session so messages posted in that channel route directly to that session. If your gateway config supports this (check `channels.bindings` or equivalent in your OpenClaw version), bind the maintainer channel to `session:clawstodian-maintainer`. The operator then chats directly in the maintainer channel and replies land straight in the heartbeat's session.

This is cleaner UX but requires gateway-level support.

## Cost profile

Per-tick cost depends on session history length:

- Fresh session (first few ticks): ~5-15K tokens.
- Steady state after a week, with `lightContext: true` and enforced compaction at `maxEntries: 300`: ~25-50K tokens.
- Without compaction, growth is linear: the session could reach 100K+ tokens after several weeks.

At 12 ticks/day in active hours, steady-state cost is ~300-600K tokens/day for the heartbeat alone. Combined with the six routine crons (~5K each, fired on their schedules), total package cost is ~400-800K tokens/day. Roughly $1-5/day depending on model pricing at time of read.

If cost is a concern, consider:

- Loosening `every` to `3h` or `4h`.
- Lowering `session.maintenance.maxEntries` (more aggressive compaction).
- Removing the `daily-retrospective` and `weekly-review` tasks from `HEARTBEAT.md` and relying on operator-triggered reviews instead.

## Troubleshooting

### No heartbeat posts appearing in the channel

1. Confirm the gateway is running and the heartbeat config loaded: `openclaw config show | grep -A5 heartbeat`.
2. Check `activeHours` - ticks outside the window skip silently.
3. Check `target` - if empty or invalid, the run may happen internally but not deliver. Gateway logs (`/tmp/openclaw/openclaw-<date>.log`) carry the reason.
4. Check the maintainer session exists: `openclaw sessions --json | grep clawstodian-maintainer`. Absent session + `isolatedSession: false` may cause routing fallback to main.
5. Check `memory/heartbeat-trace.md` - if it has recent append lines, the heartbeat is firing but delivery is failing. If it's empty, the heartbeat is not firing.
6. Review `openclaw cron list --all` for the heartbeat entry (if run via cron) or check the gateway's internal scheduler state.

### Heartbeat fires but session history isn't growing

Confirm `isolatedSession: false` in the config. If `true`, each tick is fresh and conversation history is reset.

### Session growing too fast / context window issues

Lower `session.maintenance.maxEntries` - try 200 or 150 - and bump `pruneAfter` down to 14d.

### Operator replies in the maintainer channel don't reach the next tick

Your gateway may not have channel-to-session binding for this channel. Fall back to Path 1 (`sessions_send` from the main DM agent). Document the workflow for the operator.

### Task never fires

Confirm the task name matches exactly what's in `HEARTBEAT.md`. Check `openclaw sessions --json` for the `heartbeatTaskState` map on the maintainer session - stale entries there can prevent a task from firing if its interval has not elapsed since the stored timestamp.

## See also

- `templates/HEARTBEAT.md` - the workspace-level file the heartbeat reads. Includes the `tasks:` block and detailed instructions for each task.
- `INSTALL.md` - install flow; Step 4 wires this config into the operator's OpenClaw gateway.
- `VERIFY.md` - post-install checks including maintainer-session presence.
- `UNINSTALL.md` - removal flow including session pruning.
- `docs/architecture.md` - first-principles design rationale for the collaborative-maintainer model.
- OpenClaw's own `docs/gateway/heartbeat.md` for primitive-level reference.
