# INSTALL.md

You (the installing agent) are reading this because an operator pasted an install line into their session. Your job is to install clawstodian into their workspace with their judgment, not without it.

Principle: **co-create, don't automate**. Propose diffs, wait for approval, apply, verify. Never overwrite operator content silently.

Companion docs:

- `VERIFY.md` - standalone verification checks, referenced from Step 6 below.
- `UNINSTALL.md` - full removal flow.

## Pre-flight

Confirm before touching anything:

1. You have the tools you need: Bash, file read, file write. Write a throwaway file to `/tmp` and read it back - this catches restricted-permission sessions early.
2. You know what workspace this install targets. If unclear, ask: *"Which workspace directory should I install clawstodian into? (e.g. `~/wellgent`)"*
3. The `openclaw` CLI is available and the gateway is running:
   ```bash
   openclaw --version && openclaw cron list >/dev/null
   ```
   If either fails, surface the error and stop. clawstodian uses cron flags (`--disabled`, `--light-context`, `--announce`) that require a recent OpenClaw build; if `openclaw cron add --help` does not list these flags, advise the operator to upgrade OpenClaw before proceeding.
4. The target workspace's git state is sane - not mid-rebase, not detached-HEAD, no unresolved merge conflicts. Uncommitted changes are fine; the install leaves them alone and only stages files it adds itself.
5. The operator is present to answer questions. If not, stop and ask them to return.

## Step 1 - Ensure the package is cloned

The install flow assumes clawstodian is cloned at `~/clawstodian`:

```bash
ls ~/clawstodian 2>/dev/null || echo "not present"
```

If not present, clone it. The canonical source is the wellgent org's clawstodian repo; if the operator has a fork or mirror, use theirs:

```bash
git clone https://github.com/wellgent/clawstodian.git ~/clawstodian
```

If present, check it is current:

```bash
cd ~/clawstodian && git fetch --quiet && git status
```

If the operator's clone is behind its default branch, ask whether to pull. Do not pull without asking.

## Step 2 - Read the package

Read these files in order and build a mental model of the install:

- `~/clawstodian/README.md` - scope and philosophy.
- `~/clawstodian/templates/AGENTS.md` - the workspace charter, programs catalog, and routines catalog. Installed to workspace root as `AGENTS.md`.
- `~/clawstodian/templates/HEARTBEAT.md` - the heartbeat orchestrator. Installed to workspace root as `HEARTBEAT.md`.
- `~/clawstodian/templates/para-structure.md` - PARA convention.
- `~/clawstodian/templates/daily-note-structure.md` - daily note format (includes `para_status` queue semantics).
- `~/clawstodian/templates/MEMORY.md` - dashboard skeleton.
- `~/clawstodian/templates/crons.md` - cron routine catalog.
- `~/clawstodian/templates/session-ledger.md` - starter skeleton for the session ledger. The full format spec is a section of `~/clawstodian/templates/daily-note-structure.md`; the ledger template is intentionally empty beyond its marker so a fresh workspace starts with a clean state file.

Then skim the program specs under `~/clawstodian/programs/` (domain authorities: daily-notes, para, workspace-tidy, git-hygiene) and routine specs under `~/clawstodian/routines/` (scheduled dispatchers). You do not need to copy them into the workspace - they are read on demand via the `clawstodian/programs/` and `clawstodian/routines/` symlinks created in Step 5.

All seven templates are installable workspace files: copy to the workspace and adapt as needed. Six of them are reference docs that describe workspace conventions the operator can edit (`AGENTS.md`, `HEARTBEAT.md`, `MEMORY.md`, `para-structure.md`, `daily-note-structure.md`, `crons.md`); the seventh (`session-ledger.md`) is an empty skeleton for an internal state file that only the `capture-sessions` routine writes. The format spec for the session ledger is a section of `daily-note-structure.md`, not in the skeleton. The template marker comments are optional scaffolding that lets the install detect when a template has updated; the operator can drop the markers if they prefer plain files.

## Step 3 - Survey the target workspace

Before proposing any change, read what the operator already has. Specifically check for:

1. Workspace `AGENTS.md` - does it exist? If yes, does it already contain a clawstodian section (template marker `clawstodian/agents`)? What date is the marker? Compare against `~/clawstodian/templates/AGENTS.md`'s marker date. (Legacy markers: `clawstodian/agents-section` from v0.3 / early v0.4.)
2. Workspace `HEARTBEAT.md` - does it exist? If yes, does it already contain a clawstodian section (template marker `clawstodian/heartbeat`)? What marker date? (Legacy markers: `clawstodian/heartbeat-section`.)
3. Workspace `memory/para-structure.md`, `memory/daily-note-structure.md`, `MEMORY.md`, `memory/crons.md`, `memory/session-ledger.md` - which already exist? Check marker dates.
4. Workspace PARA folders - `projects/`, `areas/`, `resources/`, `archives/`. Which already exist, which are populated?
5. Existing cron jobs - `openclaw cron list --all`. Note any clawstodian routine (`capture-sessions`, `workspace-tidy`, `git-hygiene`, `para-align`, `seal-past-days`, `para-extract`) already present, any earlier v0.4-draft routines being replaced (`daily-note`, `backfill-sessions` -> now consolidated into `capture-sessions`), and any legacy v0.3 routines (`daily-notes-tend`, `close-of-day`, `para-backfill`, `weekly-para-align`, `workspace-tidiness`, `para-tend`, `durable-insight`, `health-sweep`).
6. Current heartbeat config in `~/.openclaw/openclaw.json` (or `config.toml`). Note current `every`, `session`, `isolatedSession`, `lightContext`, `target`, `activeHours`, and channel visibility flags. See `~/clawstodian/docs/heartbeat-config.md` for the recommended stance.
7. **Session visibility config** - check `tools.sessions.visibility` in `~/.openclaw/openclaw.json`. If absent or set to `"tree"` (the default), the `capture-sessions` routine will silently capture zero content. clawstodian requires `"all"`. Note the current value so Step 4 can propose the right change.
8. Identify the operator's intended notifications channel: which channel plugin (Discord/Slack/Telegram/...) and the channel-specific recipient (e.g. `"channel:<id>"`). Heartbeat posts and cron routine announcements both land here. Distinct from the operator's DM with the agent (where collaboration happens).
9. Existing ops-* packages - check for `ops/daily/`, `ops/para/`, `ops/clean/` directories in the workspace, and for legacy cron jobs via `openclaw cron list`. Their presence is not a blocker; note it.
10. Existing workspace `clawstodian/` directory (if the workspace has a previous clawstodian install). Note which symlinks exist: v0.4 uses `clawstodian/programs` + `clawstodian/routines`; earlier drafts used only `clawstodian/routines` or only `clawstodian/programs`. Note which resolve.
11. `memory/heartbeat-trace.md` - does it exist? If not, the install will create it. If it exists, leave it; the heartbeat appends to it.

## Step 4 - Propose a merge plan

Produce a short, explicit plan for the operator. Items in the order the install should apply them:

- **AGENTS.md** (workspace root) - for each case:
  - No existing file: install `~/clawstodian/templates/AGENTS.md` verbatim.
  - Existing AGENTS.md with no clawstodian marker: propose appending the full clawstodian section from the template, or let the operator hand-merge. Warn before inserting anywhere that would reorganize existing content.
  - Existing AGENTS.md with current clawstodian marker: leave alone.
  - Existing AGENTS.md with older clawstodian marker: propose replacing just the clawstodian-marked block with the latest from the template. Warn before replacing a customized block.
- **HEARTBEAT.md** (workspace root) - same cases as AGENTS.md, using `~/clawstodian/templates/HEARTBEAT.md`. For most workspaces HEARTBEAT.md is dedicated to the orchestrator and the full template works as-is; an existing non-clawstodian HEARTBEAT.md is unusual and should prompt an explicit warning.
- **Reference templates** - for each of `memory/para-structure.md`, `memory/daily-note-structure.md`, `MEMORY.md`, `memory/crons.md`, `memory/session-ledger.md`: install from clawstodian template, skip (already exists with non-clawstodian content), or update (exists with an older clawstodian template marker). The session ledger is special-cased: if the file already exists with any H2 session entries, DO NOT overwrite it (those are real capture state). Only install if the file is absent or contains just the empty-skeleton marker.
- **PARA folders** - create missing top-level `projects/`, `areas/`, `resources/`, `archives/` if not present? (ask; some workspaces prefer different names.)
- **Workspace `clawstodian/` directory** - create it with two directory symlinks pointing at the package's `programs/` and `routines/` directories:
  ```bash
  mkdir -p clawstodian
  ln -s ~/clawstodian/programs clawstodian/programs
  ln -s ~/clawstodian/routines clawstodian/routines
  ```
  One-time setup. Program specs become reachable at `clawstodian/programs/<name>.md` and routine specs at `clawstodian/routines/<name>.md` relative to workspace root. If a legacy single symlink from an earlier draft exists (either name), remove it before adding the pair.
- **Cron routines** - install all six routines (exact commands in the **Cron install commands** section below). Scheduled (wall-clock): `para-align` (Sun 06:00 UTC), `workspace-tidy` (Sun 07:00 UTC), `git-hygiene` (01:00 and 11:00 UTC daily). Heartbeat-toggled bursts (start disabled): `capture-sessions`, `seal-past-days`, `para-extract`. Ask the operator which logs channel to deliver announcements to (Discord/Slack/Telegram channel id). Offer `--no-deliver` as alternative for workspaces that prefer silent runs.
- **Session visibility config** - set `tools.sessions.visibility: "all"` in `~/.openclaw/openclaw.json`. This is a **required prerequisite**, not optional: without it, the `capture-sessions` routine cannot see any session other than its own spawned children, so captured content is always zero. If the operator has an existing value (`"tree"`, `"agent"`, etc.), explain the trade-off before overwriting: `"all"` lets any isolated cron session in this agent see any session's transcripts. For single-operator workspaces this is the correct setting; shared-agent installs may want to scope differently and accept that clawstodian will not work out of the box.
- **Heartbeat config** - the authoritative reference is `~/clawstodian/docs/heartbeat-config.md`. Recommended stance: `every: "2h"`, `target` set to a channel plugin (`discord`, `slack`, etc.) and `to` set to the channel-specific recipient (e.g. `"channel:<id>"`) pointing at the notifications channel, `activeHours` set. Leave `session`, `isolatedSession`, and `lightContext` at their defaults so heartbeat runs in the main session with full workspace bootstrap. Do NOT add `session.maintenance`, `agents.defaults.contextPruning`, or other host-wide policy fields - those are the operator's sessions-baseline choices. Show the operator the snippet from `~/clawstodian/docs/heartbeat-config.md` and propose merging it into their OpenClaw config. Apply this last.

**If Step 3 detected legacy v0.3 routines** (programs not renamed), prepend this advisory to the plan:

> The workspace has v0.3 clawstodian routines installed (`daily-notes-tend`, `close-of-day`, etc.). v0.4 renames and consolidates these into six routines with clear single responsibilities, and introduces `memory/session-ledger.md` as the authoritative capture-state file. After installing v0.4 crons, remove the v0.3 routines via `openclaw cron remove <name>`. This install does not touch them automatically.

**If Step 3 detected ops-* packages** (directories or legacy crons), prepend this advisory to the plan:

> The workspace has `ops-daily` / `ops-para` / `ops-clean` installed. clawstodian covers the same goals via six routines. Running both pipelines in parallel is redundant but safe; you can keep ops-* running while clawstodian proves itself, then retire the legacy crons and AGENTS.md sections on your own timeline. This install will not touch ops-* state.

Present the full plan as a short bulleted list. For each item, state: current state, proposed action, why. Wait for operator approval before proceeding.

## Step 5 - Apply with confirmation

When the operator approves a specific item, apply it:

- **Installing `AGENTS.md` / `HEARTBEAT.md` templates**: copy from `~/clawstodian/templates/AGENTS.md` to workspace `AGENTS.md` (same for HEARTBEAT.md). If the workspace file already exists with other content, insert the clawstodian-marked block (everything between the `<!-- template: clawstodian/... -->` comments) at the appropriate location, preserving everything else.
- **Installing reference templates**: copy from `~/clawstodian/templates/<file>` to the workspace path. Preserve the template marker.
- **Creating PARA folders**: create the folders and add an empty `INDEX.md` in each with just `# <folder name> INDEX` as the header.
- **Creating `clawstodian/` workspace directory**: run the two-symlink commands above. Verify with `readlink clawstodian/programs` and `readlink clawstodian/routines`.
- **Adding cron routines**: run the commands from the **Cron install commands** section below, substituting `<your-logs-channel-id>`. Install in the listed order; there are no dependencies between routines.
- **Applying heartbeat config**: show the exact diff the operator would apply to their OpenClaw config, using the recommended shape from `~/clawstodian/docs/heartbeat-config.md`. For `target` + `to`: ask the operator which channel plugin and recipient to use for the dedicated notifications channel (same place cron routine announcements land; one pane for all maintenance activity). Avoid `target: "last"` - the notifications channel should be stable. Let the operator apply the diff themselves, or, with explicit confirmation, apply it for them.

Apply one item at a time. After each, verify by reading the resulting file or running the status command.

## Cron install commands

Every routine runs as its own isolated-session cron job. Commands substitute `<your-logs-channel-id>` with the operator's logs channel id. Substitute `--no-deliver` for `--announce --channel --to ...` if the operator prefers silent runs.

All six routines share these flags: `--session isolated`, `--light-context`, and `--message "Read clawstodian/routines/<name>.md and execute."` The routine spec is the authority; the cron payload is just dispatch.

**Scheduled crons** (enabled at install time, wall-clock schedules):

```bash
openclaw cron add \
  --name para-align \
  --cron "0 6 * * 0" \
  --session isolated --light-context \
  --announce --channel discord --to "channel:<your-logs-channel-id>" \
  --message "Read clawstodian/routines/para-align.md and execute."

openclaw cron add \
  --name workspace-tidy \
  --cron "0 7 * * 0" \
  --session isolated --light-context \
  --announce --channel discord --to "channel:<your-logs-channel-id>" \
  --message "Read clawstodian/routines/workspace-tidy.md and execute."

openclaw cron add \
  --name git-hygiene \
  --cron "0 1,11 * * *" \
  --session isolated --light-context \
  --announce --channel discord --to "channel:<your-logs-channel-id>" \
  --message "Read clawstodian/routines/git-hygiene.md and execute."
```

Schedule rationale:
- `para-align`: Sundays 06:00 UTC - weekly graph walk + MEMORY.md reconciliation at a quiet hour.
- `workspace-tidy`: Sundays 07:00 UTC - weekly tree sweep right after PARA align so tidying sees the reconciled structure.
- `git-hygiene`: twice daily at 01:00 and 11:00 UTC - backstop for agents who commit themselves per the program's convention. Twice-daily catches anything they missed without the 30-minute always-on noise. Operators wanting different cadence (e.g. four times a day in their active hours) can adjust the cron expression.

**Heartbeat-toggled bursts** (start disabled; heartbeat enables on demand):

```bash
openclaw cron add \
  --name capture-sessions \
  --every 30m --disabled \
  --session isolated --light-context \
  --announce --channel discord --to "channel:<your-logs-channel-id>" \
  --message "Read clawstodian/routines/capture-sessions.md and execute."

openclaw cron add \
  --name seal-past-days \
  --every 30m --disabled \
  --session isolated --light-context \
  --announce --channel discord --to "channel:<your-logs-channel-id>" \
  --message "Read clawstodian/routines/seal-past-days.md and execute."

openclaw cron add \
  --name para-extract \
  --every 30m --disabled \
  --session isolated --light-context \
  --announce --channel discord --to "channel:<your-logs-channel-id>" \
  --message "Read clawstodian/routines/para-extract.md and execute."
```

After install, verify each with:

```bash
openclaw cron list --all | grep <routine-name>
```

The smoke test in Step 6 verifies all six at once.

## Step 6 - Verify

After all selected items are applied, run the checks in `~/clawstodian/VERIFY.md`. Verify is a standalone doc that covers:

- Section markers landed in `AGENTS.md` and `HEARTBEAT.md`.
- Both workspace symlinks (`clawstodian/programs`, `clawstodian/routines`) resolve.
- All four program specs and six routine specs reachable.
- All five reference templates installed (`para-structure`, `daily-note-structure`, `MEMORY`, `crons`, `session-ledger`).
- All six cron jobs registered.
- Heartbeat config sanity (`every`, `target` + `to`, `activeHours`, `showAlerts`).
- `tools.sessions.visibility: "all"` set.
- `memory/heartbeat-trace.md` present (or prepared for first tick).

Paste the "Quick verify" block from `VERIFY.md` and report the results to the operator as a checklist. Any `FAIL` should be investigated before the first heartbeat tick fires.

**Scope note:** verify checks install-time correctness and current state. It does NOT confirm that routines deliver work over time (that is a separate audit concern, deferred).

## Step 7 - First heartbeat observation

Ask the operator whether to:

- wait for the next natural heartbeat tick, or
- trigger one manually now via `openclaw system event --text "initial heartbeat" --mode now`.

If they choose manual trigger, observe the first tick's output with them. The first tick should:

- Post a one-line executive summary to the logs channel (never silent).
- Append one line to `memory/heartbeat-trace.md`.
- Correctly identify any pending `capture-sessions`, `seal-past-days`, or `para-extract` queues and toggle those bursts accordingly. On a workspace with existing session history, `capture-sessions` will be enabled on the first tick because the ledger lags `sessions_list`; on a fresh workspace it will stay disabled until the first new session appears.
- Surface any anomalies detected in health spot-checks (including `tools.sessions.visibility` drift).

If the first tick does not post to the notifications channel, check the heartbeat config `target` (must be a registered channel plugin), `to` (must be a valid recipient for that plugin), `activeHours`, and delivery settings. A missing post is a config or wiring issue, not a silent heartbeat.

## Updating an existing install

Re-run this install flow. Step 3's survey detects which template markers are older than the package's and proposes only the needed merges. The operator approves or declines each item.

**Migrating from v0.3 to v0.4:**

- Two workspace symlinks now: `clawstodian/programs` -> `~/clawstodian/programs` and `clawstodian/routines` -> `~/clawstodian/routines`. Remove any single legacy symlink from earlier drafts; add both new ones.
- Names changed: `daily-notes-tend` -> `capture-sessions` (with semantics change - see below), `close-of-day` -> `seal-past-days`, `para-backfill` -> `para-extract`, `workspace-tidiness` -> `workspace-tidy`, `weekly-para-align` -> `para-align`.
- `capture-sessions` replaces session-capture responsibility previously split across `daily-notes-tend` (v0.3) or `daily-note` + `backfill-sessions` (earlier v0.4 drafts). One heartbeat-toggled burst does both live capture and historical drain, prioritized by `updatedAt`.
- New required config: `tools.sessions.visibility: "all"` in `~/.openclaw/openclaw.json`. Without this, session capture silently returns zero content.
- New workspace state file: `memory/session-ledger.md`. Install the template (near-empty at first). The `capture-sessions` routine populates it.
- Dropped: `para-tend`, `durable-insight`, `health-sweep` (functions folded into programs and into the heartbeat orchestrator).
- Always-on crons are now just `workspace-tidy` and `git-hygiene`. Session capture is heartbeat-toggled because agents in-session are the primary writers; the cron is a backstop that fires only when gaps exist.
- Programs vs routines: four programs (`daily-notes`, `para`, `workspace-tidy`, `git-hygiene`) under `programs/` are the domain authorities. Six routines under `routines/` are thin cron dispatchers that invoke specific behaviors from those programs.
- Heartbeat is a pure orchestrator: reads state, toggles bursts, posts summary. Does not execute programs directly.

**Migrating between v0.4 drafts** (workspaces with `daily-note` and/or `backfill-sessions` crons from an earlier draft):

- Remove the old crons: `openclaw cron remove daily-note && openclaw cron remove backfill-sessions`.
- Install the new `capture-sessions` cron (disabled, heartbeat-toggled).
- Preserve `memory/session-ledger.md` as-is; its schema is unchanged.
- The heartbeat will enable `capture-sessions` on its next tick if any gaps exist.

If a workspace has customized its `AGENTS.md` clawstodian block, leave the customization alone and only bump the marker date to match the package. Surface the customization in the plan so the operator knows their diff is preserved.

## What NOT to do

- Do not touch any file the operator has not explicitly approved.
- Do not edit `AGENTS.md` or `HEARTBEAT.md` without showing the exact diff first.
- Do not overwrite an existing reference template without marker-date comparison and confirmation.
- Do not toggle cron job enabled state beyond what each routine's install command specifies. The heartbeat manages `capture-sessions`, `seal-past-days`, and `para-extract` on/off after install.
- Do not disable, remove, or modify any legacy ops-* cron or AGENTS.md section. If the workspace has them, leave them alone.
- Do not commit any install changes to the workspace's git without operator confirmation. Leave the working tree dirty and let the maintainer routines commit on their own terms.
- Do not edit OpenClaw config directly without showing the diff.
- Do not install into a directory that is not a git repository without asking whether the operator intends for it to be one.
- Do not install into `~/` (home directory) itself.

## When in doubt

Ask. Short questions are cheaper than wrong installs.

## Uninstall

Full uninstall flow lives in `~/clawstodian/UNINSTALL.md`. Follow that doc when the operator decides to remove clawstodian. It covers disabling and removing crons, removing workspace symlinks, removing `AGENTS.md` / `HEARTBEAT.md` sections, reverting heartbeat config, optionally deleting the package clone, and explicitly flags what to leave in place (templates, workspace state, `memory/heartbeat-trace.md`).
