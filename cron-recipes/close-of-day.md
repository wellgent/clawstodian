# close-of-day cron recipe

Seals one past-day daily note per run with disk-fidelity. Starts disabled; heartbeat `daily-notes-tend` enables it when past-day notes with `status: active` exist. Self-disables when the queue is empty.

## Install

Starts disabled. Enable is handled by the heartbeat.

```bash
openclaw cron add \
  --name close-of-day \
  --every 30m \
  --disabled \
  --session isolated \
  --light-context \
  --no-deliver \
  --message "$(cat <<'PROMPT'
Seal one unsealed past-day daily note.

1. Find daily notes at `memory/YYYY-MM-DD.md` with date before today and frontmatter `status: active`, plus any past dates where `git log` shows activity but no note file exists.

2. If none found, run `openclaw cron disable close-of-day` and reply HEARTBEAT_OK.

3. Pick the oldest candidate. Seal it per `memory/daily-note-structure.md`:
   - Read raw session JSONL from disk for that date (authoritative).
   - Read `git log --since --until` for that date.
   - Merge any `memory/YYYY-MM-DD-*.md` variants into the canonical file.
   - Organize sections chronologically, consolidate duplicate topics, write a 2-3 sentence day summary, strip heartbeat and cron noise.
   - Curate frontmatter: `topics`, `people`, `projects`, `sessions`, `last_updated`.
   - Flip `status` to `sealed`.

4. Detect PARA entities per `memory/para-structure.md`. Create or update obvious placements in place. Do NOT create ambiguous ones; leave them for the heartbeat `para-tend` task to surface.

5. Update any touched `INDEX.md`.

6. If no unsealed past-day notes remain, run `openclaw cron disable close-of-day`.

Report one line: what was sealed, entities touched, ambiguities queued, whether self-disabled.

Do NOT:
- Seal more than one day per run.
- Silently file ambiguous PARA entities.
- Enable any cron.
- Commit to git.
- Overwrite a note already marked `sealed`.
PROMPT
)"
```

## Verify

```bash
openclaw cron list --all | grep close-of-day
```

Shows the job as disabled.

## Uninstall

```bash
openclaw cron remove close-of-day
```
