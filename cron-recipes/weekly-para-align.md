# weekly-para-align cron recipe

Verifies PARA structural integrity once per ISO week. Surfaces drift; does not rewrite entity content.

## Install

```bash
openclaw cron add \
  --name weekly-para-align \
  --cron "0 6 * * 0" \
  --session isolated \
  --light-context \
  --no-deliver \
  --message "$(cat <<'PROMPT'
Verify PARA structural integrity for this ISO week.

1. Walk `projects/`, `areas/`, `resources/`, `archives/`. For each entity:
   - Frontmatter matches `memory/para-structure.md`.
   - `related:` pointers resolve to existing files.
   - The entity is listed in the relevant `INDEX.md`.

2. Verify root `MEMORY.md`:
   - Active projects individually listed.
   - Retired projects not listed as active.
   - Infrastructure pointers resolve.

3. For each discrepancy:
   - Trivial structural fix (missing INDEX entry, frontmatter whitespace, obviously-inferable `last_updated`): apply in place.
   - Change to entity content, path, status, or `related` pointers: log in the summary; do NOT rewrite.

Report one short summary: entities verified, trivial fixes applied, proposals awaiting operator decision.

Do NOT:
- Rewrite entity content for style or brevity.
- Move, rename, or delete files.
- Modify `AGENTS.md`, `HEARTBEAT.md`, or any `.openclaw/` config.
- Commit to git.
PROMPT
)"
```

## Verify

```bash
openclaw cron list | grep weekly-para-align
```

## Uninstall

```bash
openclaw cron remove weekly-para-align
```
