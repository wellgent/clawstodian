<!-- template: clawstodian/memory 2026-04-18 -->
# MEMORY.md - Knowledge Graph

Curated dashboard. `INDEX.md` files have complete listings. All PARA directories are searchable via `memory_search`. Curation conventions live in `memory/para-structure.md`; the `para-align` routine keeps this file in sync with actual PARA state.

## Projects

## Areas

## Resources

## Infrastructure
- PARA conventions: `memory/para-structure.md`
- Daily note format: `memory/daily-note-structure.md`
- Cron routines and on/off state: `memory/crons.md`
- Daily notes: exactly one file per day in `memory/`, named `YYYY-MM-DD.md`. The `sessions-capture` routine merges any `YYYY-MM-DD-<slug>.md` siblings into the canonical note when it next processes a session touching that date.
