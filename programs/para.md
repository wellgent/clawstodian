# para

The workspace maintains a PARA knowledge graph - `projects/`, `areas/`, `resources/`, `archives/` - extracted from daily activity and aligned against a shared convention. Entities in PARA are the durable, searchable, structured record of what matters in this workspace.

## Who writes

**In-session agents are the primary writers and maintainers.** PARA is a live knowledge graph, not a write-once archive. During a work session, the agent both:

- **Updates existing entities** as new information surfaces - revises a project's status or next steps, records a decision or outcome on an area/person/company page, sharpens a resource with a new insight, touches `last_updated`, refreshes `related:` pointers when connections become clear.
- **Files new entities** when a new project, person, company, or reusable resource clears the thresholds in `memory/para-structure.md`.

Working with the existing graph is the more common motion; the graph is most useful when it reflects current reality.

Under cron, `para-extract` and `para-align` operate on the same graph - propagating sealed daily notes into new or existing entities and verifying structural health across the graph. Each routine has its own spec; this program defines the conventions all of them (and in-session agents) follow.

## References

- PARA conventions -> `memory/para-structure.md`
- Daily note format (source of extraction material) -> `memory/daily-note-structure.md`
- Workspace dashboard -> `MEMORY.md` at workspace root
- Daily-notes program (producer of sealed notes) -> `clawstodian/programs/daily-notes.md`

Read `memory/para-structure.md` before creating, moving, or validating entities. It defines entity types, required frontmatter, naming conventions, and `INDEX.md` maintenance rules.

## Conventions

- **Four buckets**: `projects/` (active initiatives with goals and deliverables), `areas/` (ongoing responsibilities - people, companies, servers), `resources/` (reference material - guides, insights, named patterns), `archives/` (retired content).
- **Naming**: kebab-case, lowercase, no spaces, no underscores. Per the patterns in `memory/para-structure.md`.
- **Frontmatter**: every entity has `type`, `description`, `created`, `last_updated` plus type-specific fields (`status`, `relationship`, `related`, `tags`, etc.).
- **INDEX.md per bucket**: `projects/INDEX.md`, `areas/INDEX.md`, `resources/INDEX.md` are authoritative listings. Update when creating, moving, or archiving entities.
- **MEMORY.md dashboard**: active projects are individually listed; area and resource pointers are directory-level; infrastructure section points to `memory/*.md` reference docs.
- **Creation thresholds** (per `memory/para-structure.md`): a project needs a goal, timeline, or deliverable; a person needs context in 2+ notes; a topic needs reusable knowledge; a company needs a relationship worth tracking.
- **Extraction queue marker**: sealed daily notes with `para_status: pending` are queued for PARA extraction; processed notes flip to `para_status: done`.
- **Archive candidacy is surfaced, never auto-moved.** Sustained inactivity in a project or resource (stale `last_updated`, no recent daily-note mentions, body-level indicators of completion or abandonment) makes it a candidate for archival. Detection is part of `routines/para-align.md`; the move itself is always an operator decision.

## Authority

- Create and edit files in `projects/`, `areas/`, `resources/`, `archives/` per the conventions.
- Maintain `INDEX.md` in each PARA folder.
- Update `MEMORY.md` dashboard when a new project is listed, when an active project retires, or when top-level structure drifts.
- Flip `para_status: pending -> done` on processed sealed notes.
- Apply trivial structural fixes in place: missing `INDEX.md` entry, frontmatter whitespace, obviously-inferable `last_updated`.
- Update `related:` pointers after confirmed entity renames or moves.

Must NOT reorganize existing entities without operator direction. Must NOT create stubs.

## Approval gates

- **Obvious placement -> act.** An entity clearly in bounds per `memory/para-structure.md` thresholds: a project with a stated goal and deliverable, a person mentioned with context in 2+ notes, a named resource capturing a reusable pattern.
- **Ambiguous placement -> surface.** Multiple plausible homes, crosses entity types, a new top-level folder, a rename with downstream ambiguity. In-session: ask the operator. Via cron: include in the run report.
- **Structural rewrites -> ask.** Anything beyond the trivial fixes listed in Authority.

## Escalation

- Frontmatter violations, orphaned `related:` pointers, stale `last_updated` on multiple entities: surface and propose a fix; do not silently normalize.
- A sealed source note whose content is substantively wrong (contradictory, corrupted): surface; do not attempt to rewrite.
- A rename that would update many referrers with any ambiguity in the new path: surface the proposed change set; wait.
- A structural anomaly that looks intentional (e.g. an entity was created by a plugin with non-standard shape): surface; do not correct.

## What NOT to do

- Do not rewrite entity content for style or brevity.
- Do not move, rename, or delete entity files based on your own judgment; moves are operator decisions.
- Do not auto-archive inactive projects or resources; surface archive candidates instead (detection runs in `para-align`; the move itself is an operator decision).
- Do not modify `AGENTS.md`, `HEARTBEAT.md`, or anything in `.openclaw/`.
- Do not disable or enable any cron.
- Do not create stubs.
