# INSTALL_FOR_AGENTS.md

You (the installing agent) are reading this because an operator pasted an install line into their session. Your job is to install clawstodian into their workspace with their judgment, not without it.

Principle: **co-create, don't automate**. Propose diffs, wait for approval, apply, verify. Never overwrite operator content silently.

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
- `~/clawstodian/AGENTS-SECTION.md` - the workspace charter, programs catalog, and routines catalog.
- `~/clawstodian/HEARTBEAT-SECTION.md` - the heartbeat orchestrator.
- `~/clawstodian/templates/para-structure.md` - PARA convention.
- `~/clawstodian/templates/daily-note-structure.md` - daily note format (includes `para_status` queue semantics).
- `~/clawstodian/templates/MEMORY.md` - dashboard skeleton.
- `~/clawstodian/templates/crons.md` - cron routine catalog.

Then skim the program specs under `~/clawstodian/programs/` (domain authorities: daily-notes, para, workspace-tidy, git-hygiene) and routine specs under `~/clawstodian/routines/` (scheduled dispatchers). You do not need to copy them into the workspace - they are read on demand via the `clawstodian/programs/` and `clawstodian/routines/` symlinks created in Step 5.

## Step 3 - Survey the target workspace

Before proposing any change, read what the operator already has. Specifically check for:

1. Workspace `AGENTS.md` - does it exist? If yes, does it already contain a clawstodian section (template marker `clawstodian/agents-section`)? What date is the marker? Compare against the package's `AGENTS-SECTION.md` marker date.
2. Workspace `HEARTBEAT.md` - does it exist? If yes, does it already contain a clawstodian section (template marker `clawstodian/heartbeat-section`)? What marker date?
3. Workspace `memory/para-structure.md`, `memory/daily-note-structure.md`, `MEMORY.md`, `memory/crons.md` - which already exist? Check marker dates.
4. Workspace PARA folders - `projects/`, `areas/`, `resources/`, `archives/`. Which already exist, which are populated?
5. Existing cron jobs - `openclaw cron list --all`. Note any clawstodian routine (`daily-note`, `workspace-tidy`, `git-hygiene`, `para-align`, `seal-past-days`, `para-extract`) already present, and any legacy v0.3 routines (`daily-notes-tend`, `close-of-day`, `para-backfill`, `weekly-para-align`, `workspace-tidiness`, `para-tend`, `durable-insight`, `health-sweep`).
6. Current heartbeat config in `~/.openclaw/openclaw.json` (or `config.toml`). Note current `every`, `isolatedSession`, `lightContext`, `target`, `activeHours`, and channel visibility flags.
7. Existing ops-* packages - check for `ops/daily/`, `ops/para/`, `ops/clean/` directories in the workspace, and for legacy cron jobs via `openclaw cron list`. Their presence is not a blocker; note it.
8. Existing workspace `clawstodian/` directory (if the workspace has a previous clawstodian install). Note which symlinks exist: v0.4 uses `clawstodian/programs` + `clawstodian/routines`; earlier drafts used only `clawstodian/routines` or only `clawstodian/programs`. Note which resolve.
9. `memory/heartbeat-trace.md` - does it exist? If not, the install will create it. If it exists, leave it; the orchestrator appends to it.

## Step 4 - Propose a merge plan

Produce a short, explicit plan for the operator. Items in the order the install should apply them:

- **AGENTS.md** - append the clawstodian section? Replace an existing clawstodian section if the installed marker is older than the package's? Leave alone if marker dates match. Warn before replacing a customized block where the operator has clearly reshaped the sections (memory moved out, escalation merged elsewhere).
- **HEARTBEAT.md** - create new (install clawstodian section as the whole file)? Append the clawstodian section? Replace an older version? Warn explicitly before replacing a non-empty non-clawstodian HEARTBEAT.md.
- **Reference templates** - for each of `memory/para-structure.md`, `memory/daily-note-structure.md`, `MEMORY.md`, `memory/crons.md`: install from clawstodian template, skip (already exists with non-clawstodian content), or update (exists with an older clawstodian template marker)?
- **PARA folders** - create missing top-level `projects/`, `areas/`, `resources/`, `archives/` if not present? (ask; some workspaces prefer different names.)
- **Workspace `clawstodian/` directory** - create it with two directory symlinks pointing at the package's `programs/` and `routines/` directories:
  ```bash
  mkdir -p clawstodian
  ln -s ~/clawstodian/programs clawstodian/programs
  ln -s ~/clawstodian/routines clawstodian/routines
  ```
  One-time setup. Program specs become reachable at `clawstodian/programs/<name>.md` and routine specs at `clawstodian/routines/<name>.md` relative to workspace root. If a legacy single symlink from an earlier draft exists (either name), remove it before adding the pair.
- **Cron routines** - install all six routines (exact commands in the **Cron install commands** section below). Always-on: `daily-note`, `workspace-tidy`, `git-hygiene`, `para-align`. Heartbeat-toggled bursts (start disabled): `seal-past-days`, `para-extract`. Ask the operator which logs channel to deliver announcements to (Discord/Slack/Telegram channel id). Offer `--no-deliver` as alternative for workspaces that prefer silent runs.
- **Heartbeat config** - show the recommended snippet from `~/clawstodian/README.md` ("Recommended heartbeat config") and propose merging it into the operator's OpenClaw config. Key stance: `every: 2h`, `isolatedSession: true`, `lightContext: true`, `target` pointing at the logs channel, `activeHours` set, `showAlerts: true`. The orchestrator now posts a summary every tick, so `showOk` is irrelevant (the heartbeat never replies with just `HEARTBEAT_OK`). Apply this last.

**If Step 3 detected legacy v0.3 routines** (programs not renamed), prepend this advisory to the plan:

> The workspace has v0.3 clawstodian routines installed (`daily-notes-tend`, `close-of-day`, etc.). v0.4 renames and consolidates these into six routines with clear single responsibilities. After installing v0.4 crons, remove the v0.3 routines via `openclaw cron remove <name>`. This install does not touch them automatically.

**If Step 3 detected ops-* packages** (directories or legacy crons), prepend this advisory to the plan:

> The workspace has `ops-daily` / `ops-para` / `ops-clean` installed. clawstodian covers the same goals via six routines. Running both pipelines in parallel is redundant but safe; you can keep ops-* running while clawstodian proves itself, then retire the legacy crons and AGENTS.md sections on your own timeline. This install will not touch ops-* state.

Present the full plan as a short bulleted list. For each item, state: current state, proposed action, why. Wait for operator approval before proceeding.

## Step 5 - Apply with confirmation

When the operator approves a specific item, apply it:

- **Appending to AGENTS.md or HEARTBEAT.md**: append the section verbatim from the clawstodian file. Preserve everything already in the file above and below. Include the template marker comments.
- **Installing reference templates**: copy from `~/clawstodian/templates/<file>` to the workspace path. Preserve the template marker.
- **Creating PARA folders**: create the folders and add an empty `INDEX.md` in each with just `# <folder name> INDEX` as the header.
- **Creating `clawstodian/` workspace directory**: run the two-symlink commands above. Verify with `readlink clawstodian/programs` and `readlink clawstodian/routines`.
- **Adding cron routines**: run the commands from the **Cron install commands** section below, substituting `<your-logs-channel-id>`. Install in the listed order; there are no dependencies between routines.
- **Applying heartbeat config**: show the exact diff the operator would apply to their OpenClaw config. For `target`: ask the operator for a dedicated channel ID. If they do not have one handy, default to `target: "last"` with a note that they can switch to an explicit channel later. Let them apply the diff themselves, or, with explicit confirmation, apply it for them.

Apply one item at a time. After each, verify by reading the resulting file or running the status command.

## Cron install commands

Every routine runs as its own isolated-session cron job. Commands substitute `<your-logs-channel-id>` with the operator's logs channel id. Substitute `--no-deliver` for `--announce --channel --to ...` if the operator prefers silent runs.

All six routines share these flags: `--session isolated`, `--light-context`, and `--message "Read clawstodian/routines/<name>.md and execute."` The routine spec is the authority; the cron payload is just dispatch.

**Always-on crons** (enabled at install time):

```bash
openclaw cron add \
  --name daily-note \
  --every 30m \
  --session isolated --light-context \
  --announce --channel discord --to "channel:<your-logs-channel-id>" \
  --message "Read clawstodian/routines/daily-note.md and execute."

openclaw cron add \
  --name workspace-tidy \
  --every 2h \
  --session isolated --light-context \
  --announce --channel discord --to "channel:<your-logs-channel-id>" \
  --message "Read clawstodian/routines/workspace-tidy.md and execute."

openclaw cron add \
  --name git-hygiene \
  --every 30m \
  --session isolated --light-context \
  --announce --channel discord --to "channel:<your-logs-channel-id>" \
  --message "Read clawstodian/routines/git-hygiene.md and execute."

openclaw cron add \
  --name para-align \
  --cron "0 6 * * 0" \
  --session isolated --light-context \
  --announce --channel discord --to "channel:<your-logs-channel-id>" \
  --message "Read clawstodian/routines/para-align.md and execute."
```

**Heartbeat-toggled bursts** (start disabled; heartbeat enables on demand):

```bash
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

## Step 6 - Smoke test

After all selected items are applied, run the smoke test. It verifies install-time correctness in under ten seconds. Each line is pass/fail:

```bash
# Markers in place
grep -q 'clawstodian/agents-section' AGENTS.md && echo "OK agents-section" || echo "FAIL agents-section"
grep -q 'clawstodian/heartbeat-section' HEARTBEAT.md && echo "OK heartbeat-section" || echo "FAIL heartbeat-section"

# Symlinks resolve
readlink -e clawstodian/programs >/dev/null && echo "OK programs symlink" || echo "FAIL programs symlink"
readlink -e clawstodian/routines >/dev/null && echo "OK routines symlink" || echo "FAIL routines symlink"

# Templates landed
for f in memory/para-structure.md memory/daily-note-structure.md MEMORY.md memory/crons.md; do
  [ -f "$f" ] && echo "OK template $f" || echo "MISSING template $f"
done

# Cron jobs registered (names match v0.4 catalog)
for name in daily-note workspace-tidy git-hygiene para-align seal-past-days para-extract; do
  openclaw cron list --all | grep -q " $name " && echo "OK cron $name" || echo "FAIL cron $name"
done

# Heartbeat trace file exists (or will be created on first tick)
[ -f memory/heartbeat-trace.md ] || touch memory/heartbeat-trace.md && echo "OK heartbeat-trace"
```

Report the smoke test as a checklist. Any FAIL should be investigated before the first heartbeat tick fires.

**Scope note:** the smoke test verifies install-time correctness. It does NOT verify that routines deliver their work over time (that is a separate audit concern, deferred to a later iteration). If a routine is registered and then never fires, the smoke test will still pass.

## Step 7 - First heartbeat observation

Ask the operator whether to:

- wait for the next natural heartbeat tick, or
- trigger one manually now via `openclaw system event --text "initial heartbeat" --mode now`.

If they choose manual trigger, observe the first tick's output with them. The first tick should:

- Post a one-line executive summary to the logs channel (never silent).
- Append one line to `memory/heartbeat-trace.md`.
- Correctly identify any pending `seal-past-days` or `para-extract` queues and toggle those bursts accordingly.
- Surface any anomalies detected in health spot-checks.

If the first tick does not post to the logs channel, check the heartbeat config `target`, `activeHours`, and `delivery` settings. A missing post is a config or wiring issue, not a silent heartbeat.

## Updating an existing install

Re-run this install flow. Step 3's survey detects which template markers are older than the package's and proposes only the needed merges. The operator approves or declines each item.

**Migrating from v0.3 to v0.4:**

- Two workspace symlinks now: `clawstodian/programs` -> `~/clawstodian/programs` and `clawstodian/routines` -> `~/clawstodian/routines`. Remove any single legacy symlink from earlier drafts; add both new ones.
- Names changed: `daily-notes-tend` -> `daily-note`, `close-of-day` -> `seal-past-days`, `para-backfill` -> `para-extract`, `workspace-tidiness` -> `workspace-tidy`, `weekly-para-align` -> `para-align`.
- Dropped: `para-tend`, `durable-insight`, `health-sweep` (functions folded into programs and into the heartbeat orchestrator).
- New always-on crons: `daily-note`, `workspace-tidy`, `git-hygiene` (in v0.3 these were heartbeat-direct).
- Programs vs routines: four programs (`daily-notes`, `para`, `workspace-tidy`, `git-hygiene`) under `programs/` are the domain authorities. Six routines under `routines/` are thin cron dispatchers that invoke specific behaviors from those programs.
- Heartbeat is a pure orchestrator: reads state, toggles bursts, posts summary. Does not execute programs directly.

If a workspace has customized its `AGENTS.md` clawstodian block, leave the customization alone and only bump the marker date to match the package. Surface the customization in the plan so the operator knows their diff is preserved.

## What NOT to do

- Do not touch any file the operator has not explicitly approved.
- Do not edit `AGENTS.md` or `HEARTBEAT.md` without showing the exact diff first.
- Do not overwrite an existing reference template without marker-date comparison and confirmation.
- Do not toggle cron job enabled state beyond what each routine's install command specifies. The heartbeat manages `seal-past-days` and `para-extract` on/off after install.
- Do not disable, remove, or modify any legacy ops-* cron or AGENTS.md section. If the workspace has them, leave them alone.
- Do not commit any install changes to the workspace's git without operator confirmation. Leave the working tree dirty and let the maintainer routines commit on their own terms.
- Do not edit OpenClaw config directly without showing the diff.
- Do not install into a directory that is not a git repository without asking whether the operator intends for it to be one.
- Do not install into `~/` (home directory) itself.

## When in doubt

Ask. Short questions are cheaper than wrong installs.

## Appendix - Uninstall

If the operator decides to remove clawstodian, do the reverse with confirmation at each step:

1. **Disable and remove cron routines:**
   ```bash
   for name in daily-note workspace-tidy git-hygiene para-align seal-past-days para-extract; do
     openclaw cron disable "$name" 2>/dev/null
     openclaw cron remove "$name" 2>/dev/null
   done
   ```

2. **Remove the workspace `clawstodian/` directory** (the symlink):
   ```bash
   rm -rf clawstodian
   ```

3. **Remove the clawstodian section from workspace `AGENTS.md`:** delete everything between `<!-- template: clawstodian/agents-section ... -->` and `<!-- /template: clawstodian/agents-section ... -->` inclusive.

4. **Remove the clawstodian section from workspace `HEARTBEAT.md`:** same, between the `clawstodian/heartbeat-section` markers. If `HEARTBEAT.md` is otherwise empty, either leave it or delete the file if the workspace no longer uses the heartbeat.

5. **Revert heartbeat config** in `~/.openclaw/openclaw.json` to the operator's preferred stance.

6. **Optional: delete the package clone** at `~/clawstodian` if no longer needed.

7. **Leave the reference templates and `memory/heartbeat-trace.md` alone** - they are workspace conventions and historical records that outlive clawstodian. Only remove them if the operator explicitly asks.
