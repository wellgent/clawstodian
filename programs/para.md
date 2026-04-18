# para

The workspace maintains a PARA knowledge graph - `projects/`, `areas/`, `resources/`, `archives/` - extracted from daily activity and aligned against a shared convention. Entities in PARA are the durable, searchable, structured record of what matters in this workspace.

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
- **Queue marker on source notes**: PARA extraction consumes sealed daily notes where `para_status: pending`. It flips them to `para_status: done` when complete.

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

## Behaviors

### Extract PARA from a sealed note

Propagate one sealed daily note into PARA entities. One note per invocation.

**Queue definition**. A note is queued for extraction only when all of the following are true:

- the note lives at `memory/YYYY-MM-DD.md`
- frontmatter `status: sealed`
- frontmatter `para_status: pending`

Legacy sealed notes without `para_status` are not automatically queued.

**Target selection** (for cron-driven draining of the oldest pending note):

1. List canonical daily notes where frontmatter shows `status: sealed` and `para_status: pending`.
2. Pick the **oldest** queued note.

**Steps:**

1. Read the full daily note.
2. Walk the note and detect candidate entities against `memory/para-structure.md` thresholds (projects, areas/people, areas/companies, areas/servers, resources).
3. For each candidate:
   - Obvious placement -> create or update in place.
   - Ambiguous placement -> surface without creating.
4. Update any touched `INDEX.md` files.
5. Update root `MEMORY.md` only when a new project is listed.
6. Flip the note's `para_status` from `pending` to `done`. Leave `status: sealed` unchanged. Update `last_updated`.

**Worker discipline:**

- Process one note, then stop. Do not drain multiple notes in one pass.
- Do not rewrite sealed note prose cosmetically. Touch only the frontmatter fields needed to mark queue progress.
- Do not invent `related:` pointers.
- Do not create stubs.

**Commit.** Add only the files you changed. Commit message: `para: extract YYYY-MM-DD - <summary>`. Push immediately.

### Align PARA structure

Verify and maintain PARA structural and semantic health across the full graph.

**Scope** covers four dimensions:

1. **Structural integrity** - frontmatter schema, `INDEX.md` coverage, `related:` pointer resolution.
2. **Cross-reference consistency** - when an entity moves or is renamed, every referrer updates; when an entity is deleted or archived, nothing still points at its old path.
3. **Naming and slug conventions** - kebab-case, no spaces, no underscores, lowercase; consistent with `memory/para-structure.md`.
4. **MEMORY.md currency** - every active project listed; retired projects not listed under active; infrastructure and area pointers resolve.

**Steps:**

1. **Walk the graph.** For each entity file in `projects/`, `areas/`, `resources/`, `archives/`:
   - Frontmatter matches `memory/para-structure.md`.
   - `related:` pointers resolve to existing files.
   - The entity is listed in the relevant `INDEX.md`.
   - The filename follows naming conventions.
2. **Check cross-references.**
   - For every `related:` pointer, verify the target exists at the given path.
   - For every entity path mentioned in `MEMORY.md` or in another entity's body, verify it resolves.
   - If a target moved or was renamed and the new path is unambiguous (slug differs only by known convention change), update the referrer.
   - If a target appears deleted or archived and no replacement is obvious, surface.
3. **Verify `MEMORY.md`.** Every project with `status: active` appears individually; retired or archived projects do not; infrastructure pointers resolve; top-level structure sections match reality. Rebuild the dashboard in place if drifted; the dashboard is a summary of current state, not a historical record.
4. **Classify findings.**
   - **Trivial structural fix** (missing `INDEX.md` entry, frontmatter whitespace, inferrable `last_updated`, broken `related:` pointer with obvious replacement, MEMORY.md dashboard sections out of date): apply in place.
   - **Anything else** (entity content, path, status semantics, ambiguous `related:` target, slug rename with downstream implications, new top-level folder): do NOT rewrite. Surface with file path, observed state, proposed fix.

**Commit.** Add only files you changed. Commit message: `para: align YYYY-Www - <summary>`. Push immediately.

## What NOT to do

- Do not rewrite entity content for style or brevity.
- Do not move, rename, or delete entity files based on your own judgment; moves are operator decisions.
- Do not auto-archive inactive projects (archive lifecycle is user-managed).
- Do not modify `AGENTS.md`, `HEARTBEAT.md`, or anything in `.openclaw/`.
- Do not disable or enable any cron.
- Do not batch multiple extractions in one invocation; one note per run.
- Do not create stubs.
