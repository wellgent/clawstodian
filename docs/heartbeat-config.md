# Heartbeat configuration

This is the authoritative reference for configuring clawstodian's heartbeat. The heartbeat is an OpenClaw primitive; clawstodian ships a specific recommended configuration that supports the collaborative-maintainer model: a dedicated persistent session, mixed cadence via `tasks:`, and a dedicated channel the operator watches.

The package's `templates/HEARTBEAT.md` is the workspace-level file the heartbeat reads on each tick. This doc is about the gateway-level config that wires that file into OpenClaw.

## What clawstodian uses the heartbeat for

The heartbeat is the agent's collaborative maintenance thread. On each tick, the agent:

- Reads workspace state (daily notes, `git status`, cron list, recent cron replies).
- Toggles burst workers based on queue presence.
- Posts a brief status line to the maintainer channel.
- On longer cadences: produces daily retrospectives and weekly reviews.

The heartbeat does NOT execute program behaviors. Each routine runs as its own cron job (see `INSTALL.md` "Cron install commands"). The heartbeat is an observer, toggler, and collaborator.

## Session model: why persistent named

The heartbeat can run in three session models:

- **Isolated** (`isolatedSession: true`) - fresh session every tick, no conversation history. Cheap (~2-5K tokens per tick with `lightContext: true`). The agent reconstructs context from files; it cannot remember past ticks' conversations with itself or the operator.
- **Main DM** (default, no isolation, no named session) - the heartbeat runs inside the agent's main conversation. Continuity is automatic. If the target channel is the operator's DM, bidirectional flow is free. If the target channel is a different channel (a Discord group, Slack channel), the heartbeat still runs in main DM but posts one-way to the other channel. Concern: main DM gets cluttered with maintenance directives.
- **Named persistent** (`session: "session:<name>"`) - a dedicated session reused across ticks. Continuity preserved, clean separation from the main DM. The heartbeat remembers its own past ticks. Channel replies do NOT auto-route here (see "Bidirectional flow" below).

For clawstodian's vision of a dedicated maintainer channel that stays distinct from the operator's general chat with the agent, **named persistent** is the right fit. Operator replies don't flow into the named session without a small workaround, but the heartbeat's own conversational continuity (what it said last tick, what it flagged) is preserved.

Cost is ~20-50K tokens per tick with `lightContext: false` (full bootstrap) plus a growing session history. OpenClaw ships session-maintenance defaults that bound growth automatically.

## Recommended gateway config

```json5
{
  agents: {
    defaults: {
      heartbeat: {
        every: "2h",
        session: "session:clawstodian-maintainer",
        isolatedSession: false,
        // lightContext omitted -> default false -> full workspace bootstrap loads each tick.
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

Session compaction, DM scope, reset semantics, and context pruning are NOT set here. Those are workspace-wide choices that live in the operator's `session.*` and `agents.defaults.contextPruning.*` config (see your sessions baseline). clawstodian does not override them.

### Field rationale

- **`every: "2h"`** - matches the `status` task's cadence in `templates/HEARTBEAT.md`. A tighter cadence (e.g. `30m`) wastes budget; looser (`4h`) lets queues grow longer before the agent reacts. Adjust if your workspace has different tempo.
- **`session: "session:clawstodian-maintainer"`** - dedicated persistent session. Named explicitly so the operator can inspect and prune it later. Create it once at install time (see below).
- **`isolatedSession: false`** - opt out of isolation so conversation history persists across ticks. The agent's memory of what it flagged, what it is still tracking, and the shape of the ongoing maintenance conversation all depend on this.
- **`lightContext` omitted (default `false`)** - the collaborative maintainer needs full workspace awareness every tick. `lightContext: true` would drop `AGENTS.md`, `SOUL.md`, `USER.md`, `MEMORY.md`, and daily notes, keeping only `HEARTBEAT.md`. That is the wrong trade for a maintainer that is supposed to know the workspace. Accept the ~20-50K tokens/tick cost.
- **`target`** - the maintainer channel id. Use an explicit channel (Discord/Slack/Telegram) the operator actively watches. Avoid `"last"` and `"none"` for this use case.
- **`activeHours`** - the agent's working window. Ticks outside skip silently. Match the operator's actual availability.
- **`showAlerts: true`** - deliver substantive replies.
- **`useIndicator: true`** - emit UI indicator events so compact status renders work.

### Why session-maintenance is not set here

OpenClaw has a global `session.maintenance` block (`mode`, `pruneAfter`, `maxEntries`, etc.) that defaults to `mode: "warn"`, `pruneAfter: "30d"`, `maxEntries: 500`. Those defaults are fine for the maintainer session. Prescribing `"enforce"` from the clawstodian config would silently change behavior for ALL sessions on the host, not just the maintainer. If the operator wants tighter compaction, they can set it deliberately at the host level; clawstodian does not prescribe.

### Why context-pruning / DM-scope / reset are not set here

These are host-wide policy choices the operator already made (see `claw-configs/sessions/baseline.md` or equivalent). clawstodian layers on top; it does not override the baseline.

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
4. If zero tasks are due, the tick is skipped with `reason=no-tasks-due`. (In steady state this does not happen - the 2h `status` task matches the 2h heartbeat interval, so the status task fires every tick.)

Task last-run timestamps survive across ticks in session state regardless of session model.

The prose content in `HEARTBEAT.md` below the `tasks:` block is appended as "Additional context" on every tick. That is where the detailed instructions for each task live, plus framing for the agent's role.

## Bidirectional flow: how the operator collaborates

This is the honest part. OpenClaw **does not** support direct channel-to-session binding. The heartbeat's `session` field controls where the heartbeat *runs*, not where *channel replies* route. When the operator posts in the maintainer channel, that message goes to the auto-derived session for that channel (e.g. `agent:<id>:discord:channel:<channel-id>`), **not** to `session:clawstodian-maintainer`.

There are three workable bidirectional patterns. Pick one.

### Pattern A: `sessions_send` bridge (works out of the box)

Operator DMs the agent normally ("tell the maintainer that the `para-extract` queue has been stuck for two days"). The main-session agent uses the `sessions_send` tool to inject a message into `session:clawstodian-maintainer`. The next heartbeat tick sees that message in its session context and can respond at its next post.

Latency: up to one heartbeat interval (~2h).

This is the default we document. Works with any OpenClaw setup, no extra channel or agent configuration.

### Pattern B: Main-session heartbeat, DM as maintainer channel

Skip the named session entirely. Set `session: "main"` (or omit) and `target` to the operator's DM with the agent (or whatever channel already maps to the main session). Heartbeat ticks land in the operator's DM thread; the operator replies there; next tick sees it directly.

Cost: the main DM session now carries maintenance directives intermixed with casual chat. For operators who interact primarily with the agent via DM and are comfortable with mixed context, this is the simplest bidirectional setup.

Config change from the recommended:
```json5
heartbeat: {
  // session field omitted -> main DM session used
  isolatedSession: false,
  ...
}
```

### Pattern C: Dedicated maintainer agent with channel routing

Register a second agent (e.g. `agent:maintainer`) in `agents.list` whose channel-routing rules target the dedicated maintainer channel (by Discord guild/channel id, Slack channel id, etc.). Configure that agent's heartbeat to use its own main session. Channel replies to #maintainer auto-route to that agent's channel-scoped session, which is where the heartbeat runs.

This is the cleanest separation (dedicated agent, dedicated channel, bidirectional without bridges) but requires multi-agent setup in the OpenClaw gateway config. Documented as advanced.

## Cost profile

Per-tick cost with the recommended config (`session: "session:..."`, `isolatedSession: false`, `lightContext: false`, `every: "2h"`):

- Fresh session (first few ticks): ~15-30K tokens.
- Steady state after a week, with default session-maintenance (warn mode, 500 entries): ~25-50K tokens. Token count grows as session history accumulates; auto-rotation caps it.
- Without any session maintenance, growth is linear - worth keeping an eye on via `openclaw sessions --json | grep clawstodian-maintainer`.

At 12 ticks/day in active hours, steady-state cost is ~300-600K tokens/day for the heartbeat alone. Combined with the six routine crons (~5K each, fired on their schedules), total package cost is ~400-800K tokens/day. Roughly $1-5/day depending on model pricing at time of read.

If cost is a concern, consider:

- Loosening `every` to `3h` or `4h`.
- Adding `lightContext: true` (accepts the "agent only sees HEARTBEAT.md" trade for ~2-5K tokens/tick).
- Setting an explicit `session.maintenance.mode: "enforce"` with a lower `maxEntries` globally.
- Removing `daily-retrospective` and/or `weekly-review` tasks from `HEARTBEAT.md` and relying on operator-triggered reviews instead.

## Troubleshooting

### No heartbeat posts appearing in the channel

1. Confirm the gateway is running and the heartbeat config loaded: `openclaw config show | grep -A5 heartbeat`.
2. Check `activeHours` - ticks outside the window skip silently.
3. Check `target` - if empty or invalid, the run may happen internally but not deliver. Gateway logs (`/tmp/openclaw/openclaw-<date>.log`) carry the reason.
4. Check the maintainer session exists: `openclaw sessions --json | grep clawstodian-maintainer`. If absent with `isolatedSession: false`, routing may fall back.
5. Check `memory/heartbeat-trace.md` - if it has recent append lines, the heartbeat is firing but delivery is failing. If it's empty, the heartbeat is not firing.
6. Review `openclaw cron list --all` and the gateway's internal scheduler state.

### Heartbeat fires but session history isn't growing

Confirm `isolatedSession: false` in the config. If `true`, each tick is fresh and conversation history is reset. Also confirm `session` is set to the named key and not accidentally empty.

### Operator replies in the maintainer channel don't reach the next tick

Expected. Channel replies route to the auto-derived channel session, not the heartbeat's named session. Use one of the three bidirectional patterns documented above.

### Task never fires

Confirm the task name matches exactly what's in `HEARTBEAT.md`. Check `openclaw sessions --json` for the `heartbeatTaskState` map on the maintainer session - stale entries there can prevent a task from firing if its interval has not elapsed since the stored timestamp.

### Agent feels lobotomized - doesn't know the workspace

Likely `lightContext: true`. That drops AGENTS.md, MEMORY.md, and daily notes. For a collaborative maintainer, use `lightContext: false` (default) so the full bootstrap loads each tick.

## See also

- `templates/HEARTBEAT.md` - the workspace-level file the heartbeat reads. Includes the `tasks:` block and detailed instructions for each task.
- `INSTALL.md` - install flow; Step 4 wires this config into the operator's OpenClaw gateway.
- `VERIFY.md` - post-install checks including maintainer-session presence.
- `UNINSTALL.md` - removal flow including session pruning.
- `docs/architecture.md` - first-principles design rationale for the collaborative-maintainer model.
- OpenClaw's own `docs/gateway/heartbeat.md` for primitive-level reference.
- OpenClaw's `docs/channels/channel-routing.md` for agent-selection-by-channel rules (relevant for Pattern C above).
