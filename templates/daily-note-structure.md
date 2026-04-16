<!-- template: clawstodian/daily-note-structure 2026-04-16 -->
# Daily Note Structure

Single source of truth for the daily note model. The daily-notes program (defined in `AGENTS.md` under clawstodian) reads this file. Customize per workspace as needed.

## Overview

Daily notes live at `memory/YYYY-MM-DD.md`. Each file represents exactly one calendar day. Content flows in from session transcripts, git activity, and workspace changes via the heartbeat `daily-notes-tend` task. Past days are sealed with disk-fidelity by the `close-of-day` cron burst when it is enabled.

**One canonical file per day.** The primary daily note is always `memory/YYYY-MM-DD.md`. Topic-suffixed variants such as `memory/YYYY-MM-DD-foo.md` may appear during active sessions but must be merged into the canonical note when the day is sealed. Sealed notes never have topic-suffixed siblings.

```
heartbeat daily-notes-tend (every 2h)     close-of-day cron burst
-------------------------------------     -----------------------
appends new content to today's note       seals yesterday (or older) with
from sessions_list + sessions_history     disk JSONL fidelity; merges any
+ git log; status: active                 topic-suffixed variants; status: sealed
```

## Frontmatter

```yaml
---
date: 2026-04-16
status: active
last_updated: 2026-04-16T17:30Z
topics:
  - VPS migration and OpenClaw install
  - 1Password secrets management investigation
people: [Alice, Bob]
projects: [project-a, project-b]
sessions: [96a0c068, b513d1a5]
---
```

### Fields

- `date` - the date this note covers (`YYYY-MM-DD`).
- `status` - `active` while the day is still receiving content, `sealed` after `close-of-day` has finalized it.
- `last_updated` - ISO timestamp of the most recent write.
- `topics` - 3 to 8 short phrases. Specific enough to be useful, brief enough to scan.
- `people` - real people mentioned. Test: remove the name. Does the section lose something?
- `projects` - project names, lowercase, matching workspace conventions.
- `sessions` - 8-character prefixes of session files that contributed content to this date.

### Status transitions

- `active` - day is current or recent; content still arriving; heartbeat `daily-notes-tend` may append.
- `sealed` - day has been closed by `close-of-day`; no further appends. Only material corrections allowed, and only with operator approval.

## Note Structure

```markdown
---
(frontmatter)
---
# YYYY-MM-DD

Day summary - 2 to 3 sentences. What was this day about? Key outcomes.

---

## Descriptive topic - specific detail (~HH:MM UTC)

Content...

## Another topic (~HH:MM-HH:MM UTC)

Content...
```

### Rules

- Chronological order. Sections ordered by timestamp, earliest first.
- One section per topic. Multiple sessions on the same topic consolidate into one section.
- Descriptive headers. Searchable by `memory_search`. Include topic or project name, what happened, and timestamp.
- No duplicates. Overlapping content is merged, keeping the most complete version.
- No ops noise. Daily notes capture what happened, not which heartbeat ticks ran.
- Day summary after the date heading. Human-readable narrative, not a bullet list.
- Separator: `---` between the day summary and the first topic section.

## What to Capture

Include:
- Decisions and their rationale.
- Config or infrastructure changes.
- People with meaningful context.
- Project milestones.
- Problems and solutions.
- Learnings and workflow insights.
- Behavioral corrections from the user ("do not do X", "always do Y").

Skip:
- Greetings and acknowledgments.
- Temporary states.
- Raw tool output.
- Heartbeat or cron noise.
- Content already captured in a previous session.

## What Sealing Does

Sealing is purely editorial. No entity extraction, no `INDEX.md` updates. Entity extraction is handled by the PARA program in a separate tick.

On seal:
- Merge any topic-suffixed variants into the canonical note.
- Organize sections into chronological order.
- Merge duplicate sections from overlapping sessions.
- Remove noise (tick digests, pipeline status).
- Write descriptive, searchable headers.
- Write a day summary.
- Curate frontmatter (topics, people, projects).
- Add thread-continuity markers when topics span days.
- Flip `status` from `active` to `sealed`.

**Trivial-day fast-path:** a day with 2 or fewer sections and under 1 KB of body content seals by flipping `status` without further editorial work.
