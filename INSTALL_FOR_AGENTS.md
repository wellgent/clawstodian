# INSTALL_FOR_AGENTS.md

You (the installing agent) are reading this because an operator pasted an install line into their session. Your job is to install clawstodian into their workspace with their judgment, not without it.

Principle: **co-create, don't automate**. Propose diffs, wait for approval, apply, verify. Never overwrite operator content silently.

## Pre-flight

Confirm the following before touching anything:

1. You are running in a session with access to the operator's local filesystem (Bash-capable, able to read and write files).
2. You know what workspace this install targets. If unclear, ask: *"Which workspace directory should I install clawstodian into? (e.g. `~/wellgent`)"*
3. The operator is present to answer questions. If not, stop and ask them to return.

## Step 1 - Clone the package (if not already present)

Check for an existing clone:

```bash
ls ~/clawstodian 2>/dev/null || echo "not present"
```

If not present, clone:

```bash
git clone https://github.com/<org>/clawstodian.git ~/clawstodian
```

If present, check it is current:

```bash
cd ~/clawstodian && git fetch --quiet && git status
```

If the operator's clone is behind main, ask whether to pull. Do not pull without asking.

## Step 2 - Read the package

Read these files in order and build a mental model of the install:

- `~/clawstodian/README.md` - scope and philosophy.
- `~/clawstodian/AGENTS-SECTION.md` - the charter + six programs.
- `~/clawstodian/HEARTBEAT-SECTION.md` - the heartbeat loop.
- `~/clawstodian/templates/para-structure.md` - PARA convention.
- `~/clawstodian/templates/daily-note-structure.md` - daily note format.
- `~/clawstodian/templates/MEMORY.md` - dashboard skeleton.
- `~/clawstodian/templates/crons.md` - cron recipe catalog.
- `~/clawstodian/cron-recipes/close-of-day.md` - close-of-day burst.
- `~/clawstodian/cron-recipes/weekly-para-align.md` - weekly align burst.

## Step 3 - Survey the target workspace

Before proposing any change, read what the operator already has. Specifically check for:

1. Workspace `AGENTS.md` - does it exist? If yes, does it already contain a clawstodian section (template marker `clawstodian/agents-section`)?
2. Workspace `HEARTBEAT.md` - does it exist? If yes, does it already contain a clawstodian section (template marker `clawstodian/heartbeat-section`)?
3. Workspace `memory/para-structure.md`, `memory/daily-note-structure.md`, `MEMORY.md`, `memory/crons.md` - which already exist?
4. Workspace PARA folders - `projects/`, `areas/`, `resources/`, `archives/`. Which already exist, which are populated?
5. Existing cron jobs - `openclaw cron list`. Note any `close-of-day` or `weekly-para-align` jobs already present.
6. Current heartbeat config - `~/.openclaw/config.*` or wherever the operator keeps it. Note current `every`, `isolatedSession`, `target`, `activeHours`, and channel heartbeat visibility flags (`showOk`, `showAlerts`, `useIndicator`).

## Step 4 - Propose a merge plan

Produce a short, explicit plan for the operator that covers:

- **AGENTS.md** - append the clawstodian section? Replace an existing clawstodian section if template-marker version is older? Leave alone if identical?
- **HEARTBEAT.md** - create new (install clawstodian section as the whole file)? Append the clawstodian section? Replace an older version of the section?
- **Reference templates** - for each of `memory/para-structure.md`, `memory/daily-note-structure.md`, `MEMORY.md`, `memory/crons.md`: install from clawstodian template, skip (already exists with non-clawstodian content), or update (exists with an older clawstodian template marker)?
- **PARA folders** - create missing top-level `projects/`, `areas/`, `resources/`, `archives/` if not present? (ask; some workspaces may prefer different names)
- **Heartbeat config** - show the recommended snippet from `~/clawstodian/README.md` ("Recommended heartbeat config") and propose merging it into the operator's config. Do not edit config directly without confirmation.
- **Cron recipes** - the two cron jobs are opt-in. Offer both, ask which to install. `close-of-day` starts disabled and is enabled by the heartbeat on demand; `weekly-para-align` is a plain scheduled job.

Present the plan as a short bulleted list. For each item, state: current state, proposed action, why. Wait for operator approval before proceeding.

## Step 5 - Apply with confirmation

When the operator approves a specific item, apply it:

- **Appending to AGENTS.md or HEARTBEAT.md**: append the section verbatim from the clawstodian file. Preserve everything already in the file above and below. Include the template marker comment.
- **Installing reference templates**: copy from `~/clawstodian/templates/<file>` to the workspace path. Preserve the template marker.
- **Creating PARA folders**: create the folders and add an empty `INDEX.md` in each with just `# <folder name> INDEX` as the header.
- **Applying heartbeat config**: show the exact diff the operator would apply to their OpenClaw config. Let them apply it themselves, or, with explicit confirmation, apply it for them via the openclaw CLI.
- **Adding cron recipes**: the `cron-recipes/*.md` file contains the exact `openclaw cron add` invocation. Run it only with operator confirmation. Each recipe specifies whether it starts disabled or enabled.

Apply one item at a time. After each, verify by reading the resulting file or running the status command.

## Step 6 - Verify the install

Confirm:

1. `AGENTS.md` contains the `clawstodian/agents-section` marker.
2. `HEARTBEAT.md` contains the `clawstodian/heartbeat-section` marker and a parseable `tasks:` block.
3. All agreed-upon reference templates exist at expected paths with their markers.
4. Heartbeat config matches the recommended stance.
5. If cron recipes installed: they exist, are disabled, and show in `openclaw cron list`.

Report the verification as a short checklist to the operator.

## Step 7 - First heartbeat observation

Ask the operator whether to:

- wait for the next natural heartbeat tick, or
- trigger one manually now via `openclaw system event --text "initial heartbeat" --mode now`.

If they choose manual trigger, observe the first tick's output with them. Answer any questions about what the agent did. Note the first tick will have few due tasks (most intervals haven't elapsed yet) - that is expected.

## What NOT to do

- Do not touch any file the operator has not explicitly approved.
- Do not edit `AGENTS.md` or `HEARTBEAT.md` without showing the exact diff first.
- Do not overwrite an existing reference template without marker-version comparison and confirmation.
- Do not toggle cron job enabled state beyond what each recipe's install command specifies. The heartbeat manages `close-of-day` on/off after install.
- Do not commit any install changes to the workspace's git without operator confirmation. Leave the working tree dirty and let the maintainer loop commit on its own terms.
- Do not edit OpenClaw config directly without showing the diff.
- Do not install into a directory that is not a git repository without asking whether the operator intends for it to be one.
- Do not install into `~/` (home directory) itself.

## When in doubt

Ask. Short questions are cheaper than wrong installs.
