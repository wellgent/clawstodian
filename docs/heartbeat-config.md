# Heartbeat configuration

This is the authoritative reference for configuring clawstodian's heartbeat. The heartbeat is an OpenClaw primitive; clawstodian ships a specific recommended configuration that supports the collaborative-maintainer model: heartbeat runs in the agent's main session (where the operator already collaborates with the agent by DM), and posts highlights / status / anomalies to a **dedicated notifications channel** for observability.

The package's `templates/HEARTBEAT.md` is the workspace-level file the heartbeat reads on each tick. This doc is about the gateway-level config that wires that file into OpenClaw.

## Two surfaces, two purposes

Clean separation:

- **Main session (operator's DM with the agent)** - where **collaboration** happens. The heartbeat runs here on its interval. It inherits the full main-session conversation, including everything the operator has said to the agent. When the heartbeat ticks, its work becomes part of the same thread; the operator can reply naturally and the next tick sees that reply. This is the agent's maintenance thread with the operator - scrum master, PM, chief of staff.
- **Notifications channel (dedicated)** - where **observability** happens. The heartbeat posts a combined summary per tick (header + per-task lines, with a `reflect` narrative on the daily tick). Cron routines post their own run reports to the same channel. The operator glances at it to see the running state of the workspace. It is read-mostly; replies there do not come back to the agent (channel replies would go to the channel's own auto-derived session, not the main session).

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

- **`every: "2h"`** - matches the `tend-sessions-capture` task's cadence in `templates/HEARTBEAT.md`. A tighter cadence (e.g. `30m`) wastes budget; looser (`4h`) lets the session-capture queue grow longer before the agent reacts. Adjust for your workspace tempo.
- **`session`** (omitted) - heartbeat runs in the agent's main session by default. The operator's DM with the agent IS the maintenance thread. No named session to create, no session-routing to configure.
- **`isolatedSession`** (omitted, default `false`) - conversation history persists across ticks as a natural consequence of running in the main session.
- **`lightContext`** (omitted, default `false`) - full workspace bootstrap loads each tick: `AGENTS.md` (programs catalog), `MEMORY.md` (dashboard), daily notes, any other bootstrap files the workspace uses. The maintainer is fully workspace-aware every tick.
- **`target`** - channel plugin name (`discord`, `slack`, `telegram`, `whatsapp`, `bluebubbles`, ...), or `"last"` for last-contact, or `"none"` to run internally without delivery. For the notifications channel, use the plugin that hosts it.
- **`to`** - channel-specific recipient within `target`. For Discord/Slack/Telegram channels, this is typically `"channel:<channel-id>"`. For SMS/iMessage it is a phone number. Match whatever shape the cron routines use for `--to` so heartbeat and routines land in the same place. One pane for all maintenance observability.
- **`activeHours`** - the agent's working window. Ticks outside skip silently. Match the operator's actual availability, AND see "Aligning active hours with scheduled crons" below - the start time should sit after the overnight scheduled routines finish so the first daily tick sees their fresh reports.
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

`templates/HEARTBEAT.md` ships with a `tasks:` YAML block containing four tasks: `tend-sessions-capture` (2h), `tend-daily-seal` (24h), `tend-para-extract` (24h), `reflect` (24h). Each tick:

1. The gateway parses the `tasks:` block.
2. For each task, it checks if `now >= lastRun + interval` using per-task state stored in the session entry's `heartbeatTaskState`.
3. Only due tasks are included in the batched prompt sent to the model.
4. If zero tasks are due, the tick is skipped with `reason=no-tasks-due`. (In steady state this does not happen - the 2h `tend-sessions-capture` task matches the 2h heartbeat interval, so it fires every tick.)

Task last-run timestamps survive across ticks in session state.

The prose content in `HEARTBEAT.md` below the `tasks:` block is appended as "Additional context" on every tick. It carries the orchestrator mental model, the channel post shape, and the tick-trace format. Each task prompt is light and references the routine spec it tends; the routine owns its own procedure.

## Aligning active hours with scheduled crons

OpenClaw's heartbeat task intervals are **elapsed-time** (`24h`, `2h`), not wall-clock cron expressions. A 24h-interval task fires on the first active-hours tick after 24h has passed since its last fire; once a task has fired, its daily slot stays at (roughly) the same wall-clock time until the gateway goes down and re-anchors.

This means `tend-daily-seal`, `tend-para-extract`, and `reflect` each land at some fixed time of day - determined by when the task first fired, not by operator preference. The important question is **whether that fixed time sits upstream or downstream of the scheduled routines** whose reports those tasks consume.

Recommended stance: **set `activeHours.start` at least 30-60 minutes after the latest overnight scheduled cron's wall-clock time.** With clawstodian's defaults:

- `git-clean`: 01:00 UTC
- `health-check`: 03:00 UTC
- `git-clean`: 11:00 UTC (second firing, during active hours)
- `para-align`: Sunday 06:00 UTC
- `workspace-clean`: Sunday 07:00 UTC

`activeHours.start: "04:00"` (or `"08:00"` for a later workday) guarantees the first daily tick always has the overnight `git-clean` and `health-check` reports ready for `reflect` / `tend-*` to scan. On Sundays, the weekly routines finish before a typical 08:00 start too.

Why this matters: `reflect` scans "new memory/runs/*/*.md since the previous reflect", so in absolute terms no data is missed - but if `reflect` fires at 02:00 UTC it reports on yesterday and catches up the overnight cron reports only on the next day's firing. A later `activeHours.start` keeps the daily narrative aligned with the calendar day it summarizes.

Why not fight this with wall-clock scheduling of heartbeat tasks: OpenClaw does not accept cron expressions in `interval:` (see the parser at `src/auto-reply/heartbeat.ts:196` - it accepts duration strings like `30m`, `2h`, `24h`). The first fire of each 24h task anchors its daily slot; there is no way to pin a task to, say, `"08:00 UTC"` declaratively. Operator config (active-hours + scheduled-cron times) is the only lever.

Operators with unusual workflows can adjust either side: move `health-check` earlier (e.g. `"0 0 * * *"` at midnight) to widen the alignment window, or push `activeHours.start` later to match a night-owl schedule. The invariant to preserve is: **`activeHours.start` sits at or after the last overnight scheduled cron's finish time.**

## How collaboration actually works

The operator DMs the agent normally. The agent inherits the full DM history on every response. When the heartbeat fires (every 2h within active hours), it runs in that same session - reads the workspace state, reviews the recent conversation, runs whichever tasks are due, and posts a combined summary to the notifications channel. It may also append notes to the main DM conversation for items that need the operator's attention (the daily `reflect` task explicitly does this), or wait for the operator to notice the notifications-channel post and come back to DM.

Because the heartbeat and the operator share the main session, the agent naturally remembers:

- What it flagged in the last tick's summary.
- What the operator replied to (in the DM) and what remains unanswered.
- In-flight investigations and follow-ups.
- Anything the operator mentioned between ticks.

No `sessions_send` bridge. No channel-to-session binding. The main session is already the collaboration space; the heartbeat just makes sure the agent checks in on workspace state regularly.

## Notifications channel

The channel resolved by `target` + `to` receives:

- Heartbeat posts: combined tick summary (every tick - header + per-task lines for whichever tasks fired). The daily tick additionally carries a `reflect` narrative.
- Per-routine announcements from the seven cron routines (`sessions-capture`, `daily-seal`, `para-extract`, `para-align`, `workspace-clean`, `git-clean`, `health-check`). Each routine runs in its own isolated cron session and posts a multi-line scannable run report via `--announce --channel --to`.

This gives one unified pane of maintenance activity. An operator glancing at the channel sees: "heartbeat tick at 10:00, git-clean committed 3 things at 11:00, health-check all-ok at 03:00, heartbeat daily `reflect` at noon, etc."

Channel replies in this channel do NOT route back to the main session. OpenClaw routes channel messages to the channel's auto-derived session (e.g. `agent:<id>:discord:channel:<id>`), not the agent's main DM session. So the notifications channel is effectively read-only for the maintenance conversation. If the operator wants to discuss something they see there, they do so in DM with the agent.

## Cost profile

Per-tick cost with the recommended config (main session, `lightContext: false`, `every: "2h"`):

- Fresh workspace (minimal main-session history): ~15-30K tokens.
- Steady state: grows with main session history. Typical workspaces in active use: ~40-80K tokens per heartbeat tick.
- Without any session maintenance enforcement, growth is linear; the operator's host-wide `session.maintenance` policy (or the OpenClaw defaults) caps it eventually.

At 8-12 ticks/day in active hours, steady-state cost is ~300-1000K tokens/day for the heartbeat alone. Combined with the six routine crons (~5K each for the always-on / fixed workers in isolated sessions; `sessions-capture` can cost 10-30K per firing when session activity is high, and only fires when gaps exist), total maintenance cost is ~400K-1.2M tokens/day in active workspaces. Roughly $1-8/day depending on model pricing. On disciplined workspaces where agents write daily notes in-session, `sessions-capture` may go days between firings and overall cost drops further.

If cost becomes a concern:

- Loosen `every` to `3h` or `4h`.
- Set `lightContext: true` (accepts the trade of the maintainer only seeing `HEARTBEAT.md` at bootstrap).
- Tighten host-wide `session.maintenance` to `enforce` mode with a lower `maxEntries`.
- Remove the `reflect` task from `HEARTBEAT.md` and rely on operator-triggered reviews instead.

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

- `templates/HEARTBEAT.md` - the workspace-level file the heartbeat reads. Includes the `tasks:` block, the orchestrator mental model, and the channel / trace conventions. Task prompts are light; procedure lives in the referenced routine specs.
- `INSTALL.md` - install flow; Step 4 wires this config into the operator's OpenClaw gateway.
- `VERIFY.md` - post-install checks.
- `UNINSTALL.md` - removal flow.
- `docs/architecture.md` - first-principles design rationale for the collaborative-maintainer model.
- OpenClaw's own `docs/gateway/heartbeat.md` for primitive-level reference.
- OpenClaw's `docs/channels/channel-routing.md` for how inbound channel messages resolve to sessions.
