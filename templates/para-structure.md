<!-- template: clawstodian/para-structure 2026-04-18 -->
# PARA Conventions

Single source of truth for how the knowledge graph is organized in this workspace. The `para-extract` and `para-align` routines (defined in `AGENTS.md` under clawstodian) read this file when creating, moving, or validating entities. Customize per workspace as needed; keep the structural rules intact.

## What is PARA?

A four-tier organization system for all workspace knowledge:

```
projects/       active initiatives with goals and deadlines
areas/          ongoing responsibilities (people, topics, companies)
resources/      notes, references, guides, and insights
archives/       deactivated projects, retired content
memory/         daily notes (YYYY-MM-DD.md) + reference docs
```

Daily notes are the raw input. PARA entities are the structured output: durable knowledge extracted from daily activity. All PARA directories and `memory/` are semantically searchable via `memory_search`.

## Creation thresholds

Create an entity when:
- A person is mentioned with context in 2 or more notes (not just a name drop).
- A project has a clear goal, timeline, or deliverable.
- A topic produces reusable knowledge (guide, reference, insight).
- A company has a relationship worth tracking (client, prospect, partner).

Do not create stubs. If you cannot write substantive content, do not create the file. If placement is ambiguous, ask the operator before creating.

## Navigation Layers

### MEMORY.md (workspace root)

Curated dashboard. Not an exhaustive catalog. Contains:
- All active projects (individually listed).
- Key area pointers (directory-level).
- Infrastructure pointers (all `memory/*.md` reference docs).

Curation rule: `MEMORY.md` grows slowly. New projects always get listed. Areas get directory-level pointers only.

### INDEX.md (one per PARA folder, searchable)

Complete index of everything in that folder. Pure listings. No conventions, no templates.

- `projects/INDEX.md` - all projects with status and one-liner.
- `areas/INDEX.md` - all area entities.
- `resources/INDEX.md` - notes and references.

Maintenance rule: after creating, moving, or archiving any PARA entity, update the relevant `INDEX.md` in the same tick.

### Per-project or per-area README.md

Project-specific or area-specific orientation. Status, goals, file map.

Exists at: `projects/*/README.md`, `areas/*/README.md` when a directory crosses 3 or more files.

## Frontmatter Specification

Every PARA file has YAML frontmatter.

### Types

- `project` in `projects/`
- `person` in `areas/people/`
- `company` in `areas/companies/`
- `area` for READMEs and orientation docs within `areas/`
- `resource` for notes and references in `resources/`

### Filename Conventions

- Projects: `projects/<name>/README.md` - lowercase, hyphenated.
- People: `areas/people/<firstname-lastname>.md` - first-name-only when unambiguous.
- Companies: `areas/companies/<name>.md` - lowercase, hyphenated.
- Resources: `resources/<descriptive-name>.md` - lowercase, hyphenated.

### Common Fields

Every entity has these four fields:

- `type` - one of the values above. Set once at creation.
- `description` - one sentence, present tense. Should work as an `INDEX.md` entry.
- `created` - date the file was created (`YYYY-MM-DD`).
- `last_updated` - last processed or reviewed date (`YYYY-MM-DD`).

### Type-Specific Fields

**project:**
- `status` - `active` | `on-hold` | `completed` | `archived`
- `repos` - GitHub `org/repo` format. Omit if no code.
- `urls` - deployed or live URLs. Omit if none.
- `tags` - cross-cutting topics.
- `related` - file paths to related PARA entities.

**person:**
- `status` - `active` | `archived`
- `company` - current employer or org. Omit if N/A.
- `role` - job title or description. Omit if unknown.
- `relationship` - `friend` | `client` | `prospect` | `partner` | `contact`
- `related` - company entity, related projects.

**company:**
- `status` - `active` | `archived`
- `relationship` - `client` | `partner` | `prospect` | `vendor`
- `url` - company website.
- `industry` - plain text.
- `related` - key people, related projects.

**area** - common fields only.

**resource:**
- `tags` - cross-cutting topics.

### Field Rules

- `status` - use exact values listed per type. No synonyms.
- `related` - file paths relative to workspace root. Direct structural relationships only.
- `tags` - only on `project` and `resource`.

## General Rules

- Knowledge lives where it will be read. No standalone "lessons learned" files.
- Date-prefix temporal files: `YYYY-MM-DD-` for instant age visibility.
- Subfolders when a category grows large: 10 or more items gets its own subfolder.
- Update in place, do not delete. Git provides the audit trail.
- Docs describe the present. No decision history, no "added on date X" annotations.

## README and INDEX Hygiene

- `INDEX.md` files are authoritative listings for PARA folders. Update when creating, moving, or archiving entities.
- `README.md` files provide per-project and per-area orientation. Not placed at the PARA folder level.
- Create a `README.md` inside a project or area directory once it crosses 3 or more files.
