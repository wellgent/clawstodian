<!-- template: clawstodian/heartbeat-section 2026-04-16 -->
# Heartbeat checklist

This file is read fresh every heartbeat tick. OpenClaw parses the `tasks:` block and only runs tasks whose interval has elapsed. Everything below guides what the agent does when a task is due.

The authority and boundaries for each action live in `AGENTS.md` under the clawstodian programs. This file is the operational loop.

tasks:

- name: daily-notes-tend
  interval: 2h
  prompt: |
    Tend today's daily note and capture durable insights from recent activity. Then check whether a close-of-day cron burst is needed.

    Part A - today's note:
    1. Determine today's date (workspace local timezone). Target file: `memory/YYYY-MM-DD.md`.
    2. Gather inputs since the last tick-of-this-task: `sessions_list` filtered to today, `sessions_history` for normalized content from each, `git log --since` for the same window.
    3. If the note does not exist, create it following `memory/daily-note-structure.md` with `status: active`.
    4. If the note exists, append new sections in chronological order. Do not rewrite existing sections cosmetically. Update frontmatter: `last_updated`, `topics`, `people`, `projects`, `sessions`.

    Part B - durable insight capture:
    1. Review what you just added to today's note and any untracked insights from recent sessions.
    2. For each candidate insight, decide: obvious placement (existing entity or a clearly-named new one) -> file it per `memory/para-structure.md`. Ambiguous placement -> batch for the tick summary and ask the operator.
    3. If a candidate would require a new top-level folder or a new type of entity, do not create it; surface it.

    Part C - close-of-day orchestration:
    1. Look for daily notes in `memory/` with dates before today whose frontmatter `status` is still `active` (or are missing entirely for days that had activity).
    2. If any exist and the `close-of-day` cron is currently disabled, enable it: `openclaw cron enable close-of-day`.
    3. If none exist and `close-of-day` is currently enabled, disable it: `openclaw cron disable close-of-day`.

    Tick summary format (one short message):
    - "filed: <paths>; asked: <questions>; enabled/disabled: <crons>" - or `HEARTBEAT_OK` if nothing happened.

- name: para-tend
  interval: 4h
  prompt: |
    Process one recent sealed daily note for PARA extraction.

    1. List daily notes in `memory/` with `status: sealed`.
    2. Identify entities in each note's frontmatter (`people`, `projects`, `topics`) and compare against entity files' `last_updated`. Pick the sealed note with the most unpropagated entity updates, or the oldest sealed note whose referenced entities are out of date.
    3. For each referenced entity: if the entity file exists, update it in place with new context. If it doesn't and placement is obvious (per thresholds in `memory/para-structure.md`), create it. If placement is ambiguous, batch for the tick summary and ask the operator.
    4. Update `INDEX.md` in any PARA folder touched. Update root `MEMORY.md` only when a new project is listed.

    Tick summary format:
    - "extracted from <note>; updated/created: <entities>; asked: <questions>" - or `HEARTBEAT_OK`.

- name: workspace-sweep
  interval: 6h
  prompt: |
    Run tidiness, git hygiene, and health sweep in one pass. Each is its own program in `AGENTS.md`; they share the same tick because they all inspect the workspace.

    Part A - tidiness:
    1. Find empty directories without `.gitkeep`, stale run-logs older than 30 days, broken symlinks, and scratch files the agent created that are no longer referenced.
    2. Obvious actions: remove. Non-obvious (unfamiliar directory, files of unknown origin, any binary >1MB): batch for operator.

    Part B - git hygiene:
    1. `git status`. If clean, skip.
    2. Group dirty files into logical commits - one concern per commit. Stage by exact path. Commit with workspace-style messages. No AI attribution lines. No `--no-verify`.
    3. For new ephemeral patterns (caches, logs, build output), add to `.gitignore` and commit that. Non-obvious new files: ask.
    4. Stop and surface if the tree is mid-rebase, detached, or conflicted.

    Part C - health sweep:
    1. Check `openclaw cron list` for recently failed runs; report the last 1-2 failure reasons per failing job.
    2. Compare installed reference templates (`memory/para-structure.md`, `memory/daily-note-structure.md`, `MEMORY.md`, `memory/crons.md`) to the clawstodian repo copies for drift.
    3. Verify heartbeat config still matches the recommended stance (`isolatedSession: true`, `target` set to a real channel, `activeHours` set, `showOk: false` + `showAlerts: true` on channel heartbeat visibility).
    4. Verify workspace symlinks resolve.
    5. Report findings with likely causes and proposed resolutions. Do not auto-repair configs or templates.

    Tick summary format:
    - "tidied: <count>; committed: <commit subjects>; surfaced: <findings>; asked: <questions>" - or `HEARTBEAT_OK`.

# Additional instructions

- Execute-Verify-Report: after any action, verify by reading the resulting state. Do not assume success.
- Co-create: when placement, filing, or risk is ambiguous, ask the operator in one short question. When obvious, just do it.
- Batch signalling: produce exactly one short summary message per tick across all due tasks. Not one per action.
- Quiet by default: if a tick produced no meaningful change, reply `HEARTBEAT_OK`.
- Surface emerging projects or workstreams in the tick summary with a proposed filing. Do not silently create them.
- Escalate before destructive, risky, or ambiguous changes - see cross-program escalation rules in `AGENTS.md`.
- Never commit with AI attribution (`Co-Authored-By`, `Generated by`, etc.).
- Never use `--no-verify`, `git reset --hard`, `git clean -f`, or force-push.
- If no due task needs attention, reply `HEARTBEAT_OK`.

<!-- /template: clawstodian/heartbeat-section 2026-04-16 -->
