# INSTALL_FOR_AGENTS.md

You (the installing agent) are reading this because an operator pasted an install line into their session. Your job is to install clawstodian into their workspace with their judgment, not without it.

Principle: **co-create, don't automate**. Propose diffs, wait for approval, apply, verify. Never overwrite operator content silently.

## Pre-flight

Confirm the following before touching anything:

1. You have the tools you need: Bash, file read, file write. A one-line sanity check - write a throwaway file to `/tmp` and read it back - catches restricted-permission sessions early.
2. You know what workspace this install targets. If unclear, ask: *"Which workspace directory should I install clawstodian into? (e.g. `~/wellgent`)"*
3. The `openclaw` CLI is available and the gateway is running. Quick test:
   ```bash
   openclaw --version && openclaw cron list >/dev/null
   ```
   If either fails, surface the error and stop. The install needs a running gateway to register crons and verify heartbeat behavior. clawstodian uses cron flags (`--disabled`, `--light-context`, `--no-deliver`) that require a recent OpenClaw build; if `openclaw cron add --help` does not list these flags, advise the operator to upgrade OpenClaw before proceeding.
4. The target workspace's git state is sane - not mid-rebase, not detached-HEAD, no unresolved merge conflicts. Uncommitted changes are fine; the install will leave them alone and only stage files it adds itself.
5. The operator is present to answer questions. If not, stop and ask them to return.

## Step 1 - Ensure the package is cloned

The install flow assumes the clawstodian repo is cloned at `~/clawstodian`. Check:

```bash
ls ~/clawstodian 2>/dev/null || echo "not present"
```

If not present, ask the operator for the clone source (GitHub URL or another path) and clone to `~/clawstodian`:

```bash
git clone <URL-FROM-OPERATOR> ~/clawstodian
```

If present, check it is current:

```bash
cd ~/clawstodian && git fetch --quiet && git status
```

If the operator's clone is behind its default branch, ask whether to pull. Do not pull without asking.

## Step 2 - Read the package

Read these files in order and build a mental model of the install:

- `~/clawstodian/README.md` - scope and philosophy.
- `~/clawstodian/AGENTS-SECTION.md` - the charter + six programs.
- `~/clawstodian/HEARTBEAT-SECTION.md` - the heartbeat loop.
- `~/clawstodian/templates/para-structure.md` - PARA convention.
- `~/clawstodian/templates/daily-note-structure.md` - daily note format.
- `~/clawstodian/templates/MEMORY.md` - dashboard skeleton.
- `~/clawstodian/templates/crons.md` - cron routine catalog.
- `~/clawstodian/cron-routines/close-of-day.md` - close-of-day burst.
- `~/clawstodian/cron-routines/para-backfill.md` - sealed-note PARA backfill burst.
- `~/clawstodian/cron-routines/weekly-para-align.md` - weekly align burst.

## Step 3 - Survey the target workspace

Before proposing any change, read what the operator already has. Specifically check for:

1. Workspace `AGENTS.md` - does it exist? If yes, does it already contain a clawstodian section (template marker `clawstodian/agents-section`)?
2. Workspace `HEARTBEAT.md` - does it exist? If yes, does it already contain a clawstodian section (template marker `clawstodian/heartbeat-section`)?
3. Workspace `memory/para-structure.md`, `memory/daily-note-structure.md`, `MEMORY.md`, `memory/crons.md` - which already exist?
4. Workspace PARA folders - `projects/`, `areas/`, `resources/`, `archives/`. Which already exist, which are populated?
5. Existing cron jobs - `openclaw cron list`. Note any `close-of-day`, `para-backfill`, or `weekly-para-align` jobs already present.
6. Current heartbeat config - typically `~/.openclaw/config.toml` or `~/.openclaw/config.json`. If not at a standard path, ask the operator where it lives. Note current `every`, `isolatedSession`, `target`, `activeHours`, and channel heartbeat visibility flags (`showOk`, `showAlerts`, `useIndicator`).
7. Existing ops-* packages - check for `ops/daily/`, `ops/para/`, `ops/clean/` directories in the workspace, and for legacy cron jobs via `openclaw cron list` (names starting with `daily-`, `para-`, `clean-`). Their presence is not a blocker; note it so Step 4 can surface the overlap.

## Step 4 - Propose a merge plan

Produce a short, explicit plan for the operator. Items in the order the install should apply them:

- **AGENTS.md** - append the clawstodian section? Replace an existing clawstodian section if template-marker version is older? Leave alone if identical?
- **HEARTBEAT.md** - create new (install clawstodian section as the whole file)? Append the clawstodian section? Replace an older version of the section? Warn explicitly before replacing a non-empty non-clawstodian HEARTBEAT.md.
- **Reference templates** - for each of `memory/para-structure.md`, `memory/daily-note-structure.md`, `MEMORY.md`, `memory/crons.md`: install from clawstodian template, skip (already exists with non-clawstodian content), or update (exists with an older clawstodian template marker)?
- **PARA folders** - create missing top-level `projects/`, `areas/`, `resources/`, `archives/` if not present? (ask; some workspaces may prefer different names)
- **Workspace `clawstodian/` directory** - create it with symlinks to the package's cron-routine files so the crons can reference them via short workspace-relative paths. Prerequisite for any cron routine install; a one-time setup.
- **Cron routines** - the cron jobs are opt-in. Offer the routines the operator wants. `close-of-day` starts disabled and is enabled by the heartbeat on demand, `para-backfill` starts disabled and is enabled by the heartbeat when sealed-note backlog exists, and `weekly-para-align` is a plain scheduled job.
- **Heartbeat config** - show the recommended snippet from `~/clawstodian/README.md` ("Recommended heartbeat config") and propose merging it into the operator's config. If the workspace already has heartbeat enabled with different settings, compare current vs. proposed field-by-field and let the operator choose which values to adopt (some operators have workspace-specific cadence or active-hours they want to keep). Apply this last, after the workspace has everything the heartbeat will need.

**If Step 3 detected ops-* packages** (directories or legacy crons), prepend this advisory to the plan:

> The workspace has `ops-daily` / `ops-para` / `ops-clean` installed. clawstodian covers the same goals via the six programs. Running both pipelines in parallel is redundant but safe; you can keep ops-* running while clawstodian proves itself in this workspace, then retire the legacy crons and AGENTS.md sections on your own timeline. This install will not touch ops-* state.

Present the full plan as a short bulleted list. For each item, state: current state, proposed action, why. Wait for operator approval before proceeding.

## Step 5 - Apply with confirmation

When the operator approves a specific item, apply it:

- **Appending to AGENTS.md or HEARTBEAT.md**: append the section verbatim from the clawstodian file. Preserve everything already in the file above and below. Include the template marker comment.
- **Installing reference templates**: copy from `~/clawstodian/templates/<file>` to the workspace path. Preserve the template marker.
- **Creating PARA folders**: create the folders and add an empty `INDEX.md` in each with just `# <folder name> INDEX` as the header.
- **Creating `clawstodian/` workspace directory**: run `mkdir -p clawstodian && ln -sf ~/clawstodian/cron-routines/close-of-day.md clawstodian/close-of-day.md && ln -sf ~/clawstodian/cron-routines/para-backfill.md clawstodian/para-backfill.md && ln -sf ~/clawstodian/cron-routines/weekly-para-align.md clawstodian/weekly-para-align.md` from the workspace root. The symlinks let cron `--message` use short workspace-relative paths like `"Read clawstodian/close-of-day.md and execute."`.
- **Adding cron routines**: follow the `## Install` section in each routine file (e.g. `~/clawstodian/cron-routines/close-of-day.md`). The install command is ready to run as-is; just execute it with operator confirmation. Each routine specifies whether it starts disabled or enabled.
- **Applying heartbeat config**: show the exact diff the operator would apply to their OpenClaw config. For `target`: ask the operator for a dedicated channel ID (Telegram chat ID, Slack channel ID, Discord channel ID) - this is the recommended setup. If they do not have one handy, default to `target: "last"` with a note that they can switch to an explicit channel later. Let them apply the diff themselves, or, with explicit confirmation, apply it for them via the openclaw CLI.

Apply one item at a time. After each, verify by reading the resulting file or running the status command.

## Step 6 - Verify the install

Confirm:

1. `AGENTS.md` contains the `clawstodian/agents-section` marker.
2. `HEARTBEAT.md` contains the `clawstodian/heartbeat-section` marker and a parseable `tasks:` block.
3. All agreed-upon reference templates exist at expected paths with their markers.
4. Heartbeat config matches the recommended stance.
5. If the workspace `clawstodian/` directory was created: it exists and the symlinks resolve (`readlink clawstodian/*.md` should point inside `~/clawstodian/cron-routines/`).
6. If cron routines installed: they exist and show in `openclaw cron list` (with the expected `enabled` state per routine).

Report the verification as a short checklist to the operator (one line per item with `OK` / `FAIL` and, on failure, a one-line reason).

## Step 7 - First heartbeat observation

Ask the operator whether to:

- wait for the next natural heartbeat tick, or
- trigger one manually now via `openclaw system event --text "initial heartbeat" --mode now`.

If they choose manual trigger, observe the first tick's output with them. Answer any questions about what the agent did. Note the first tick will have few due tasks (most intervals haven't elapsed yet) - that is expected.

## What NOT to do

- Do not touch any file the operator has not explicitly approved.
- Do not edit `AGENTS.md` or `HEARTBEAT.md` without showing the exact diff first.
- Do not overwrite an existing reference template without marker-version comparison and confirmation.
- Do not toggle cron job enabled state beyond what each routine's install command specifies. The heartbeat manages `close-of-day` on/off after install.
- Do not disable, remove, or modify any legacy ops-* cron or AGENTS.md section. If the workspace has them, leave them alone and let the operator retire them on their own timeline.
- Do not commit any install changes to the workspace's git without operator confirmation. Leave the working tree dirty and let the maintainer loop commit on its own terms.
- Do not edit OpenClaw config directly without showing the diff.
- Do not install into a directory that is not a git repository without asking whether the operator intends for it to be one.
- Do not install into `~/` (home directory) itself.

## When in doubt

Ask. Short questions are cheaper than wrong installs.

## Appendix: Uninstall

If the operator decides to remove clawstodian, do the reverse of the install with confirmation at each step:

1. **Disable and remove cron routines:**

   ```bash
   openclaw cron disable close-of-day && openclaw cron remove close-of-day
   openclaw cron disable para-backfill && openclaw cron remove para-backfill
   openclaw cron disable weekly-para-align && openclaw cron remove weekly-para-align
   ```

2. **Remove the workspace `clawstodian/` directory** (the symlinks):

   ```bash
   rm -rf clawstodian
   ```

3. **Remove the clawstodian section from workspace `AGENTS.md`:** delete everything between the opening marker `<!-- template: clawstodian/agents-section ... -->` and closing marker `<!-- /template: clawstodian/agents-section ... -->` (inclusive).

4. **Remove the clawstodian section from workspace `HEARTBEAT.md`:** same, between the `clawstodian/heartbeat-section` markers. If `HEARTBEAT.md` is otherwise empty, either leave it (the heartbeat will reply `HEARTBEAT_OK` every tick) or delete the file if the workspace no longer uses the heartbeat.

5. **Revert heartbeat config** in `~/.openclaw/config.*` to the operator's preferred stance.

6. **Optional: delete the package clone** at `~/clawstodian` if no longer needed.

7. **Leave the reference templates alone** - `memory/para-structure.md`, `memory/daily-note-structure.md`, `MEMORY.md`, and `memory/crons.md` are workspace conventions that outlive clawstodian. Only remove them if the operator explicitly asks.
