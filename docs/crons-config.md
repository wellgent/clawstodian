# Cron jobs configuration

This is the authoritative reference for configuring clawstodian's cron routines. OpenClaw's cron primitive is the execution substrate; clawstodian ships a specific flag stack per routine so every job runs with sensible isolation, delivery, and timeouts.

The install commands in `INSTALL.md` > "Cron install commands" are the concrete invocation; this doc is the rationale behind what those `openclaw cron add` calls pass. The workspace-installed `templates/crons.md` is the operator dashboard, not the config source.

## Shared flags

All seven clawstodian routines register with the same base flag stack:

- **`--session isolated`** - each run gets a dedicated cron session (`agent:<agent>:cron:<jobId>`). No main-session history inherited; next run starts fresh. Routines that need cross-run memory use files under `memory/` (run reports, session ledger, daily notes), not session state.
- **`--light-context`** - skip the full workspace bootstrap (`AGENTS.md`, `MEMORY.md`, daily notes, ...) when assembling the isolated session. Each routine reads its own spec from `clawstodian/routines/<name>.md` and whatever else it needs on demand. Keeps per-firing cost bounded and predictable.
- **`--announce --channel <plugin> --to "channel:<id>"`** - post the routine's multi-line summary to the notifications channel. Same target the heartbeat uses, so the operator has one pane for all maintenance activity.
- **`--message "Read clawstodian/routines/<name>.md and execute."`** - the cron payload is a dispatch pointer; the routine spec is the authority. Spec updates take effect without re-registering crons.

## Flags clawstodian deliberately does NOT set

These exist and are sometimes useful, but clawstodian leaves them at the agent's default:

- **`--thinking`** (reasoning level: `off` / `minimal` / `low` / `medium` / `high` / `xhigh`) - routines that need deeper reasoning (`para-align`'s judgment calls, `daily-seal`'s editorial pass) benefit from the agent's standard thinking budget; prescribing it per-job creates cost drift and surprise.
- **`--model`** (model override) - the operator's sessions baseline chooses the model; each routine should follow. Operators who want aggressive budget control (e.g. cheap model for `git-clean`) can override per-job after install.
- **`--tz`** (timezone for cron expressions) - all clawstodian cron expressions are UTC; leaving `--tz` unset uses the gateway host's default (UTC for typical deployments). Operators running local-time crons set it per-routine when editing.
- **`--stagger` / `--exact`** - leave at default. OpenClaw automatically staggers top-of-hour expressions by up to 5 min to reduce load spikes. Clawstodian routines do not require exact timing.
- **`--session-key`** - `--session isolated` alone produces a stable per-job session key automatically (`agent:<agent>:cron:<jobId>`). Overriding creates drift across runs.
- **`--best-effort-deliver`** - see "Delivery failures" below.

## Timeouts

OpenClaw's `--timeout` default is **30 seconds (`30000` ms)** - far too short for agent-driven routines that read JSONL transcripts, walk the PARA graph, or do an editorial seal pass. Clawstodian uses the longer `--timeout-seconds <n>` flag (designed for agent jobs) with a tailored ceiling per routine:

- **`sessions-capture`: `1800` (30 min)** - processes up to 5 interactive sessions per firing, each 20-100 KB of filtered JSONL. Soft stop at ~140K tokens of consumed context. The 30-min ceiling absorbs pathological historical-drain firings on first install; steady state finishes in minutes.
- **`daily-seal`: `1200` (20 min)** - editorial pass on one note. Fast-path trivial days finish in seconds; full-seal on a busy day runs read + organize + curate + write end-to-end and can take several minutes.
- **`para-extract`: `1200` (20 min)** - reads PARA indices, walks candidate subjects in one sealed note, updates existing entities + creates new ones. Cost dominated by per-entity reads and writes.
- **`para-align`: `1800` (30 min)** - weekly full-graph walk: `projects/`, `areas/`, `resources/`, `archives/` + greps across 7 days (semantic freshness) and 30 days (archive candidacy) of sealed daily notes.
- **`workspace-clean`: `900` (15 min)** - weekly tree walk + dotfile audit + anomaly sweep. Tree-walk cost grows with workspace size; the routine caps its own work.
- **`git-clean`: `600` (10 min)** - stage-by-path commits + push. Typically a handful of files per firing; the ceiling absorbs noisy days.
- **`health-check`: `300` (5 min)** - pure read-only checks (config, `cron list`, symlinks, marker grep, report-timestamp reads). Finishes in seconds on a healthy workspace; the ceiling covers slow network-mounted installs.

These are **ceilings, not targets**. On quiet days every routine finishes in a fraction of its timeout.

A timeout trip is a hard failure for that firing: the run is marked failed and openclaw's exponential retry (30s → 1m → 5m → 15m → 60m) kicks in. Persistent timeouts surface through `health-check` as a stalled routine; investigate before bumping the ceiling further.

## Retry behavior

OpenClaw's cron primitive owns retries; clawstodian does not configure them.

- **Transient errors** (rate-limit, overload, network, server-error) retry up to **3 times** within the firing with exponential backoff.
- **Recurring job errors** use exponential retry backoff across firings: 30s → 1m → 5m → 15m → 60m. Backoff resets after the next successful run.
- **Permanent errors** disable the job - at which point operator intervention is required. `health-check` catches this by observing that the cron is no longer firing.

Defaults live in openclaw's `cron.retry.*` config (`cron.retry.maxAttempts`, `cron.retry.backoffMs`, `cron.retry.retryOn`). Operators rarely need to touch them.

## Delivery failures

`--best-effort-deliver` tells openclaw to mark the job successful even if channel delivery fails. Without it, a channel outage marks the firing as failed, tripping the retry backoff and eventually disabling the job on persistent failures.

Every clawstodian routine writes its run-report file to `memory/runs/<routine>/<ts>.md` **before** attempting channel delivery. The channel post is a convenience; the file is the authoritative record. That means **`--best-effort-deliver` is safe** - a delivery outage never loses the report.

The default install does NOT enable it, so delivery outages are visible in the operator's failure feed. Operators with flaky channel plugins (self-hosted Matrix, Slack rate-limits, etc.) can opt in per-routine after install:

```bash
openclaw cron edit <routine-name> --best-effort-deliver
```

## Alignment with the heartbeat

The scheduled-cron wall-clock times (`git-clean` 01:00 UTC, `health-check` 03:00 UTC, weekly `para-align` Sun 06:00, weekly `workspace-clean` Sun 07:00) are deliberately placed **before** a typical operator's `activeHours.start` so the first daily heartbeat tick sees the overnight reports.

See `docs/heartbeat-config.md` > "Aligning active hours with scheduled crons" for the full rationale. Short version: **`activeHours.start` must sit at or after the last overnight scheduled cron's finish time.** With clawstodian defaults, `activeHours.start: "04:00"` (or later) is the invariant.

If the operator changes cron times (e.g. runs `health-check` at midnight), they must re-check the `activeHours.start` alignment.

## Editing config after install

After install, cron jobs are owned by `~/.openclaw/cron/jobs.json`, not by any file in the workspace. **Changes to `INSTALL.md` or `templates/crons.md` do NOT propagate automatically.**

To change an installed job's flag:

```bash
openclaw cron edit <routine-name> --timeout-seconds 3600
openclaw cron edit <routine-name> --best-effort-deliver
openclaw cron edit <routine-name> --no-deliver
```

Or remove + re-add from the commands in `INSTALL.md`. `health-check` verifies that the expected seven routines are registered, but does not verify individual flag values; the operator owns the correctness of per-routine settings after install.

## Cost profile

Per-firing cost (approximate, with default stance: `--session isolated --light-context`, main agent model, default thinking):

- **`sessions-capture`** - **5-30K tokens** typical. Dominated by filtered JSONL reads (small input, small output). Historical-drain firings on first install can reach 100K.
- **`daily-seal`** - **10-30K tokens** typical. Trivial-day fast-path is under 5K.
- **`para-extract`** - **10-30K tokens** typical. Reads PARA indices + one sealed note + N entity files; writes updates.
- **`para-align`** - **30-80K tokens** weekly. Full-graph walk + cross-reference check + freshness / archive greps.
- **`workspace-clean`** - **5-15K tokens** weekly. Mostly tree walks and frontmatter reads.
- **`git-clean`** - **3-10K tokens** per firing. Small model turns commit drift into staged groups.
- **`health-check`** - **3-10K tokens** daily. Read-only; finishes fast.

Combined: on a disciplined workspace (agents write daily notes in-session, most burst routines stay disabled most of the day), total cron cost runs **~100-400K tokens/day** across all seven routines. Roughly $0.50-3/day depending on model pricing. See `docs/heartbeat-config.md` > "Cost profile" for the heartbeat side of the ledger.

## Troubleshooting

### A routine has not fired recently

`health-check` reports routines that have not written a run-report in 2x their expected interval. Investigate:

```bash
openclaw cron list --all | grep <routine-name>
openclaw cron runs --id <job-id> --limit 20
```

Look for: disabled flag, retry backoff from repeated failures, permanent error, gateway downtime. Re-enable with `openclaw cron enable <routine-name>` once the cause is understood.

### A burst cron stays enabled too long

Indicates the routine can't drain its queue within expected time. `health-check` flags bursts enabled > 12h (`sessions-capture`) or > 24h (`daily-seal` / `para-extract`) with non-shrinking queue.

Check the routine's recent `memory/runs/<routine>/*.md` for the queue-size trajectory; if each firing completes but the queue grows, the inflow is outpacing the routine. Adjust the heartbeat `every` to something tighter, or investigate what's creating the backlog.

### A timeout keeps tripping

Check `memory/runs/<routine>/*.md` for what the routine was doing when it hit the ceiling. Typical causes: an unusually large JSONL transcript, a pathologically branched PARA walk, a commit involving hundreds of files. Fix at the source (shrink the input, handle the pathological case in the routine spec) before raising the ceiling.

### Delivery succeeds but the message does not appear

`--announce --channel <plugin> --to "channel:<id>"` must use a registered channel plugin and a recipient that plugin understands. See openclaw's `docs/automation/cron-jobs.md` > "Delivery and output" for per-plugin recipient shapes.

## See also

- `INSTALL.md` > "Cron install commands" - the concrete `openclaw cron add` invocations.
- `templates/crons.md` - workspace-installed operator dashboard.
- `docs/heartbeat-config.md` - paired gateway-level heartbeat config reference.
- `docs/writing-a-routine.md` > "Install command conventions" - authoring rules for adding a new routine.
- OpenClaw's `docs/automation/cron-jobs.md` - primitive-level reference.
- OpenClaw's `docs/cli/cron.md` - CLI reference (flags, subcommands, config).
