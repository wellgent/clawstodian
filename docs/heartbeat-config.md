# Heartbeat configuration

This is the authoritative reference for configuring clawstodian's heartbeat. The heartbeat is an OpenClaw primitive; clawstodian ships a specific recommended configuration that supports the collaborative-maintainer model: heartbeat runs in the agent's main session (where the operator already collaborates with the agent by DM), and posts highlights / status / anomalies to a **dedicated notifications channel** for observability.

The package's `templates/HEARTBEAT.md` is the workspace-level file the heartbeat reads on each tick. This doc is about the gateway-level config that wires that file into OpenClaw.

## Two surfaces, two purposes

Clean separation:

- **Main session (operator's DM with the agent)** - where **collaboration** happens. The heartbeat runs here on its interval. It inherits the full main-session conversation, including everything the operator has said to the agent. When the heartbeat ticks, its work becomes part of the same thread; the operator can reply naturally and the next tick sees that reply. This is the agent's maintenance thread with the operator - scrum master, PM, chief of staff.
- **Notifications channel (dedicated)** - where **observability** happens. The heartbeat posts one line per tick: status summary, daily retrospectives, weekly reviews. Cron routines post their own one-line run reports to the same channel. The operator glances at it to see the running state of the workspace. It is read-mostly; replies there do not come back to the agent (channel replies would go to the channel's own auto-derived session, not the main session).

The split matches how OpenClaw's channel routing actually works. Main-session inheritance gives collaborative continuity for free. A dedicated target channel gives a single pane of workspace activity without polluting the main DM with per-routine noise.

## Recommended gateway config

```json5
{
  agents: {
    defaults: {
      heartbeat: {
        every: "2h",
        // session omitted -> main session (default) -> collaborative continuity with the operator
        // isolatedSession omitted -> false (default)
        // lightContext omitted -> false (default) -> full workspace bootstrap each tick
        target: "discord", // channel plugin: discord | slack | telegram | whatsapp | bluebubbles | last | none
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

clawstodian deliberately does NOT set `session.maintenance`, `agents.defaults.contextPruning`, `session.dmScope`, or `session.reset` - those are host-wide policy choices the operator makes at the sessions-baseline level. The heartbeat config layers on top without overriding.

### Field rationale

- **`every: "2h"`** - matches the `status` task's cadence in `templates/HEARTBEAT.md`. A tighter cadence (e.g. `30m`) wastes budget; looser (`4h`) lets queues grow longer before the agent reacts. Adjust for your workspace tempo.
- **`session`** (omitted) - heartbeat runs in the agent's main session by default. The operator's DM with the agent IS the maintenance thread. No named session to create, no session-routing to configure.
- **`isolatedSession`** (omitted, default `false`) - conversation history persists across ticks as a natural consequence of running in the main session.
- **`lightContext`** (omitted, default `false`) - full workspace bootstrap loads each tick: `AGENTS.md` (programs catalog), `MEMORY.md` (dashboard), daily notes, any other bootstrap files the workspace uses. The maintainer is fully workspace-aware every tick.
- **`target`** - channel plugin name (`discord`, `slack`, `telegram`, `whatsapp`, `bluebubbles`, ...), or `"last"` for last-contact, or `"none"` to run internally without delivery. For the notifications channel, use the plugin that hosts it.
- **`to`** - channel-specific recipient within `target`. For Discord/Slack/Telegram channels, this is typically `"channel:<channel-id>"`. For SMS/iMessage it is a phone number. Match whatever shape the cron routines use for `--to` so heartbeat and routines land in the same place. One pane for all maintenance observability.
- **`activeHours`** - the agent's working window. Ticks outside skip silently. Match the operator's actual availability.
- **`showAlerts: true`** - deliver substantive replies.
- **`useIndicator: true`** - emit UI indicator events.

### Why these fields are NOT set here

OpenClaw has these host-wide policy fields; clawstodian does not prescribe them:

- **`session.maintenance`** - compaction / pruning / rotation for the session store. OpenClaw defaults (`mode: "warn"`, `pruneAfter: "30d"`, `maxEntries: 500`) apply. The operator can set `enforce` mode at the host level if they want aggressive compaction.
- **`agents.defaults.contextPruning`** - prompt-cache-based context pruning within a session. Whatever the operator's sessions baseline chose.
- **`session.dmScope`** - DM isolation strategy (`main`, `per-peer`, `per-channel-peer`). Baseline choice.
- **`session.reset`** - idle reset policy for sessions. Baseline choice.

The logic: clawstodian layers a maintenance pattern onto whatever session posture the workspace already has. Overriding these would surprise the operator.

## How `tasks:` interacts with the config

`templates/HEARTBEAT.md` ships with a `tasks:` YAML block containing three tasks: `status` (2h), `daily-retrospective` (24h), `weekly-review` (168h / weekly). Each tick:

1. The gateway parses the `tasks:` block.
2. For each task, it checks if `now >= lastRun + interval` using per-task state stored in the session entry's `heartbeatTaskState`.
3. Only due tasks are included in the batched prompt sent to the model.
4. If zero tasks are due, the tick is skipped with `reason=no-tasks-due`. (In steady state this does not happen - the 2h `status` task matches the 2h heartbeat interval, so the status task fires every tick.)

Task last-run timestamps survive across ticks in session state.

The prose content in `HEARTBEAT.md` below the `tasks:` block is appended as "Additional context" on every tick. That is where the detailed instructions for each task live, plus framing for the agent's role.

## How collaboration actually works

The operator DMs the agent normally. The agent inherits the full DM history on every response. When the heartbeat fires (every 2h within active hours), it runs in that same session - reads the workspace state, reviews the recent conversation, decides what to act on, and posts its status line to the notifications channel. It may also append notes to the main DM conversation for items that need the operator's attention, or wait for the operator to notice the notifications-channel post and come back to DM.

Because the heartbeat and the operator share the main session, the agent naturally remembers:

- What it flagged in the last tick's status post.
- What the operator replied to (in the DM) and what remains unanswered.
- In-flight investigations and follow-ups.
- Anything the operator mentioned between ticks.

No `sessions_send` bridge. No channel-to-session binding. The main session is already the collaboration space; the heartbeat just makes sure the agent checks in on workspace state regularly.

## Notifications channel

The channel resolved by `target` + `to` receives:

- Heartbeat posts: status (every tick), daily retrospective (once/day), weekly review (once/week).
- Per-routine announcements from the six cron routines (`daily-note`, `workspace-tidy`, `git-hygiene`, `para-align`, `seal-past-days`, `para-extract`). Each routine runs in its own isolated cron session and posts a single-line run report via `--announce --channel --to`.

This gives one unified pane of maintenance activity. An operator glancing at the channel sees: "heartbeat status at 10:00, git-hygiene committed 3 things at 10:15, daily-note merged a slug sibling at 11:00, heartbeat daily retrospective at noon, etc."

Channel replies in this channel do NOT route back to the main session. OpenClaw routes channel messages to the channel's auto-derived session (e.g. `agent:<id>:discord:channel:<id>`), not the agent's main DM session. So the notifications channel is effectively read-only for the maintenance conversation. If the operator wants to discuss something they see there, they do so in DM with the agent.

## Cost profile

Per-tick cost with the recommended config (main session, `lightContext: false`, `every: "2h"`):

- Fresh workspace (minimal main-session history): ~15-30K tokens.
- Steady state: grows with main session history. Typical workspaces in active use: ~40-80K tokens per heartbeat tick.
- Without any session maintenance enforcement, growth is linear; the operator's host-wide `session.maintenance` policy (or the OpenClaw defaults) caps it eventually.

At 8-12 ticks/day in active hours, steady-state cost is ~300-1000K tokens/day for the heartbeat alone. Combined with the six routine crons (~5K each in isolated cron sessions, fired on their schedules), total maintenance cost is ~400K-1.2M tokens/day. Roughly $1-8/day depending on model pricing.

If cost becomes a concern:

- Loosen `every` to `3h` or `4h`.
- Set `lightContext: true` (accepts the trade of the maintainer only seeing `HEARTBEAT.md` at bootstrap).
- Tighten host-wide `session.maintenance` to `enforce` mode with a lower `maxEntries`.
- Remove `daily-retrospective` and/or `weekly-review` tasks from `HEARTBEAT.md` and rely on operator-triggered reviews instead.

## Troubleshooting

### No heartbeat posts appearing in the notifications channel

1. Confirm the gateway is running and the heartbeat config loaded: `openclaw config show | grep -A5 heartbeat`.
2. Check `activeHours` - ticks outside the window skip silently.
3. Check `target` + `to` - `target` must be a registered channel plugin (`discord`, `slack`, etc.); `to` must be a recipient that plugin understands (e.g. `"channel:<id>"`). If either is wrong, the run may happen internally but not deliver. Gateway logs (`/tmp/openclaw/openclaw-<date>.log`) carry the reason.
4. Check `memory/heartbeat-trace.md` - if it has recent append lines, the heartbeat is firing but delivery is failing. If it's empty, the heartbeat is not firing at all.
5. Review the gateway's internal scheduler state.

### Heartbeat fires but the agent seems to forget past ticks

Confirm `isolatedSession` is `false` or omitted. If `true`, each tick is fresh and history resets. Also confirm `session` is not explicitly set to a named session that you forgot to create.

### Agent feels lobotomized - doesn't know the workspace

Confirm `lightContext` is `false` or omitted. `lightContext: true` drops AGENTS.md, MEMORY.md, and daily notes - everything except HEARTBEAT.md. For a collaborative maintainer, the default (`false`) is correct.

### Main session grows too large over time

Set host-wide `session.maintenance.mode: "enforce"` with a reasonable `maxEntries` (e.g. 300). This is a host-level decision; clawstodian does not prescribe it.

### Task never fires

Confirm the task name matches exactly what's in `HEARTBEAT.md`. Check `openclaw sessions --json` for the `heartbeatTaskState` map on the main session - stale entries there can prevent a task from firing if its interval has not elapsed since the stored timestamp.

### Operator reply in notifications channel goes nowhere

Expected. Channel replies route to the channel's auto-derived session, not the main session. The notifications channel is observability only. Discussion happens in the operator's DM with the agent.

## See also

- `templates/HEARTBEAT.md` - the workspace-level file the heartbeat reads. Includes the `tasks:` block and detailed instructions for each task.
- `INSTALL.md` - install flow; Step 4 wires this config into the operator's OpenClaw gateway.
- `VERIFY.md` - post-install checks.
- `UNINSTALL.md` - removal flow.
- `docs/architecture.md` - first-principles design rationale for the collaborative-maintainer model.
- OpenClaw's own `docs/gateway/heartbeat.md` for primitive-level reference.
- OpenClaw's `docs/channels/channel-routing.md` for how inbound channel messages resolve to sessions.
