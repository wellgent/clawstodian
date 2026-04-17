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
   If either fails, surface the error and stop. clawstodian uses cron flags (`--disabled`, `--light-context`, `--no-deliver`) that require a recent OpenClaw build; if `openclaw cron add --help` does not list these flags, advise the operator to upgrade OpenClaw before proceeding.
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
- `~/clawstodian/AGENTS-SECTION.md` - the charter and program catalog.
- `~/clawstodian/HEARTBEAT-SECTION.md` - the heartbeat coordinator.
- `~/clawstodian/templates/para-structure.md` - PARA convention.
- `~/clawstodian/templates/daily-note-structure.md` - daily note format.
- `~/clawstodian/templates/MEMORY.md` - dashboard skeleton.
- `~/clawstodian/templates/crons.md` - cron routine catalog.

Then skim the program specs under `~/clawstodian/programs/` so you understand what each program does. You do not need to copy them into the workspace - they are read on demand via the `clawstodian/programs/` symlink created in Step 5.

## Step 3 - Survey the target workspace

Before proposing any change, read what the operator already has. Specifically check for:

1. Workspace `AGENTS.md` - does it exist? If yes, does it already contain a clawstodian section (template marker `clawstodian/agents-section`)? What date is the marker? Compare against the package's `AGENTS-SECTION.md` marker date.
2. Workspace `HEARTBEAT.md` - does it exist? If yes, does it already contain a clawstodian section (template marker `clawstodian/heartbeat-section`)? What marker date?
3. Workspace `memory/para-structure.md`, `memory/daily-note-structure.md`, `MEMORY.md`, `memory/crons.md` - which already exist? Check marker dates.
4. Workspace PARA folders - `projects/`, `areas/`, `resources/`, `archives/`. Which already exist, which are populated?
5. Existing cron jobs - `openclaw cron list`. Note any `close-of-day`, `para-backfill`, or `weekly-para-align` jobs already present.
6. Current heartbeat config in `~/.openclaw/openclaw.json` (or `config.toml`). Note current `every`, `isolatedSession`, `target`, `activeHours`, and channel visibility flags (`showOk`, `showAlerts`, `useIndicator`).
7. Existing ops-* packages - check for `ops/daily/`, `ops/para/`, `ops/clean/` directories in the workspace, and for legacy cron jobs via `openclaw cron list` (names starting with `daily-`, `para-`, `clean-`). Their presence is not a blocker; note it so Step 4 can surface the overlap.
8. Existing workspace `clawstodian/` directory (if the workspace has a previous clawstodian install). Note whether its symlinks resolve.

## Step 4 - Propose a merge plan

Produce a short, explicit plan for the operator. Items in the order the install should apply them:

- **AGENTS.md** - append the clawstodian section? Replace an existing clawstodian section if the installed marker is older than the package's? Leave alone if marker dates match. Warn before replacing a customized block where the operator has clearly reshaped the sections (memory moved out, escalation merged elsewhere).
- **HEARTBEAT.md** - create new (install clawstodian section as the whole file)? Append the clawstodian section? Replace an older version? Warn explicitly before replacing a non-empty non-clawstodian HEARTBEAT.md.
- **Reference templates** - for each of `memory/para-structure.md`, `memory/daily-note-structure.md`, `MEMORY.md`, `memory/crons.md`: install from clawstodian template, skip (already exists with non-clawstodian content), or update (exists with an older clawstodian template marker)?
- **PARA folders** - create missing top-level `projects/`, `areas/`, `resources/`, `archives/` if not present? (ask; some workspaces prefer different names.)
- **Workspace `clawstodian/` directory** - create it with a single directory symlink that points at the package's `programs/` directory. Prerequisite for cron routines and for the `AGENTS.md` catalog references to resolve:
  ```bash
  mkdir -p clawstodian && ln -s ~/clawstodian/programs clawstodian/programs
  ```
  One-time setup. All program specs become reachable at `clawstodian/programs/<name>.md` relative to workspace root.
- **Cron routines** - the cron jobs are opt-in. Offer the routines the operator wants. `close-of-day` and `para-backfill` start disabled (heartbeat enables them on demand); `weekly-para-align` is a scheduled Sunday 06:00 job and starts enabled.
- **Heartbeat config** - show the recommended snippet from `~/clawstodian/README.md` ("Recommended heartbeat config") and propose merging it into the operator's OpenClaw config. If the workspace already has heartbeat enabled with different settings, compare field-by-field and let the operator choose which values to adopt. Apply this last.

**If Step 3 detected ops-* packages** (directories or legacy crons), prepend this advisory to the plan:

> The workspace has `ops-daily` / `ops-para` / `ops-clean` installed. clawstodian covers the same goals via the nine programs. Running both pipelines in parallel is redundant but safe; you can keep ops-* running while clawstodian proves itself, then retire the legacy crons and AGENTS.md sections on your own timeline. This install will not touch ops-* state.

Present the full plan as a short bulleted list. For each item, state: current state, proposed action, why. Wait for operator approval before proceeding.

## Step 5 - Apply with confirmation

When the operator approves a specific item, apply it:

- **Appending to AGENTS.md or HEARTBEAT.md**: append the section verbatim from the clawstodian file. Preserve everything already in the file above and below. Include the template marker comments.
- **Installing reference templates**: copy from `~/clawstodian/templates/<file>` to the workspace path. Preserve the template marker.
- **Creating PARA folders**: create the folders and add an empty `INDEX.md` in each with just `# <folder name> INDEX` as the header.
- **Creating `clawstodian/` workspace directory**: run the single-symlink command above. Verify with `readlink clawstodian/programs` - it should point at `~/clawstodian/programs/`.
- **Adding cron routines**: each routine's spec file under `~/clawstodian/programs/` includes an install command at the bottom. The cron `--message` is a one-liner pointing back to the routine file, so routine updates take effect without editing cron state. Example:
  ```
  openclaw cron add --name close-of-day --every 30m --disabled --light-context --no-deliver --message "Read clawstodian/programs/close-of-day.md and execute."
  ```
- **Applying heartbeat config**: show the exact diff the operator would apply to their OpenClaw config. For `target`: ask the operator for a dedicated channel ID (Telegram chat ID, Slack channel ID, Discord channel ID) - this is the recommended setup. If they do not have one handy, default to `target: "last"` with a note that they can switch to an explicit channel later. Let them apply the diff themselves, or, with explicit confirmation, apply it for them via the openclaw CLI.

Apply one item at a time. After each, verify by reading the resulting file or running the status command.

## Step 6 - Verify the install

Confirm:

1. `AGENTS.md` contains the `clawstodian/agents-section` marker.
2. `HEARTBEAT.md` contains the `clawstodian/heartbeat-section` marker.
3. All agreed-upon reference templates exist at expected paths with their markers.
4. Heartbeat config matches the recommended stance.
5. Workspace `clawstodian/programs` symlink resolves:
   ```bash
   readlink -e clawstodian/programs
   ```
   (should print `~/clawstodian/programs`)
6. Program specs are reachable at `clawstodian/programs/<name>.md` from the workspace root (spot-check one):
   ```bash
   ls clawstodian/programs/ | head
   ```
7. If cron routines installed: they exist and show in `openclaw cron list` (with the expected `enabled` state per routine).

Report verification as a short checklist (one line per item with `OK` / `FAIL` and, on failure, a one-line reason).

## Step 7 - First heartbeat observation

Ask the operator whether to:

- wait for the next natural heartbeat tick, or
- trigger one manually now via `openclaw system event --text "initial heartbeat" --mode now`.

If they choose manual trigger, observe the first tick's output with them. Note: the heartbeat is a pure coordinator - each tick reads workspace state fresh and decides which programs to run based on what has changed since the last tick. The first real tick will usually produce `HEARTBEAT_OK` unless there is pending work (an unsealed past-day note, a dirty git tree, a queued sealed note).

## Updating an existing install

Re-run this install flow. Step 3's survey detects which template markers are older than the package's and proposes only the needed merges. The operator approves or declines each item.

If a workspace has customized its `AGENTS.md` clawstodian block (e.g. moved memory-and-navigation or cross-program escalation out into top-level sections), leave the customization alone and only bump the marker date to match the package. Surface the customization in the plan so the operator knows their diff is preserved.

## What NOT to do

- Do not touch any file the operator has not explicitly approved.
- Do not edit `AGENTS.md` or `HEARTBEAT.md` without showing the exact diff first.
- Do not overwrite an existing reference template without marker-date comparison and confirmation.
- Do not toggle cron job enabled state beyond what each routine's install command specifies. The heartbeat manages `close-of-day` and `para-backfill` on/off after install.
- Do not disable, remove, or modify any legacy ops-* cron or AGENTS.md section. If the workspace has them, leave them alone.
- Do not commit any install changes to the workspace's git without operator confirmation. Leave the working tree dirty and let the maintainer loop commit on its own terms.
- Do not edit OpenClaw config directly without showing the diff.
- Do not install into a directory that is not a git repository without asking whether the operator intends for it to be one.
- Do not install into `~/` (home directory) itself.

## When in doubt

Ask. Short questions are cheaper than wrong installs.

## Appendix - Uninstall

If the operator decides to remove clawstodian, do the reverse with confirmation at each step:

1. **Disable and remove cron routines:**
   ```bash
   openclaw cron disable close-of-day && openclaw cron remove close-of-day
   openclaw cron disable para-backfill && openclaw cron remove para-backfill
   openclaw cron disable weekly-para-align && openclaw cron remove weekly-para-align
   ```

2. **Remove the workspace `clawstodian/` directory** (the symlink):
   ```bash
   rm -rf clawstodian
   ```

3. **Remove the clawstodian section from workspace `AGENTS.md`:** delete everything between `<!-- template: clawstodian/agents-section ... -->` and `<!-- /template: clawstodian/agents-section ... -->` inclusive.

4. **Remove the clawstodian section from workspace `HEARTBEAT.md`:** same, between the `clawstodian/heartbeat-section` markers. If `HEARTBEAT.md` is otherwise empty, either leave it (heartbeat replies `HEARTBEAT_OK` every tick) or delete the file if the workspace no longer uses the heartbeat.

5. **Revert heartbeat config** in `~/.openclaw/openclaw.json` to the operator's preferred stance.

6. **Optional: delete the package clone** at `~/clawstodian` if no longer needed.

7. **Leave the reference templates alone** - `memory/para-structure.md`, `memory/daily-note-structure.md`, `MEMORY.md`, `memory/crons.md` are workspace conventions that outlive clawstodian. Only remove them if the operator explicitly asks.
