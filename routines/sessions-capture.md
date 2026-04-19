# sessions-capture (routine)

Backstop for the daily-notes program. Captures unread interactive-session content into the right daily note(s), one session at a time, until the queue is drained.

## Program

`clawstodian/programs/daily-notes.md` - conventions, authority, approval gates, and escalation.

See `memory/daily-note-structure.md` for the daily-note format and the session-ledger format.

## Shape

The queue is determined by a pre-built script: `clawstodian/scripts/scan-sessions.py`. The script projects `openclaw sessions --json` against `memory/session-ledger.md`, classifies every visible session, and emits the pending work as JSON. This routine reads the queue, processes one session end-to-end, and loops until the queue is empty or the firing budget is spent.

**The ledger contains interactive sessions only.** Skipped classifications (cron, hook, sub-agent, dreaming, empty / delivery-only) are not stored - they are re-derived on every scan. Admission is no longer a separate step: when the script reports a new interactive session, the first capture pass creates its ledger entry with the post-write cursor.

**Orphan ledger entries are ignored** - if a ledger entry's session id is not in `sessions_list`, it's either history with a pruned transcript or stale state. Not this routine's problem; don't cross-check ledger against disk.

## Target

The output of `clawstodian/scripts/scan-sessions.py`:

- **`queue`** - interactive sessions that need attention, sorted by `updated_at` descending (newest first). Each entry has `status: new` (not in ledger yet) or `status: stale` (ledger cursor behind the transcript's current line count).
- **`missing_transcripts`** - sessions whose `transcriptPath` does not resolve on disk. Surfaced, not processed, unless `sessions_history` can reach them via the live registry.
- **`counts`** - diagnostic counts for the run report.

The script is invoked once at firing start to build the queue, once before self-disable to re-check, and optionally with `--next` to pull a single target.

## Steps

1. **Prereq read.** Read `memory/daily-note-structure.md` sections "Frontmatter", "Note Structure", "What to Capture", and "Session Ledger" into context. These are authoritative for what you write.

2. **Scan.** Invoke the classification script from the workspace root:

   ```bash
   clawstodian/scripts/scan-sessions.py > /tmp/clawstodian-sessions-capture-scan.json
   ```

   Read the JSON. If `queue` is empty, skip to step 6 (self-disable + quiet run report).

3. **Process one session.** Pick the first entry in `queue` (newest `updated_at`). Apply the unit-of-work procedure below. Advance the ledger cursor. Write any daily-note content.

4. **Budget check.** After each session, stop the loop if ANY of these hold:
   - Script reports `queue` is now empty (re-invoke to re-check - see step 6).
   - Five interactive sessions have been processed this firing (hard cap).
   - Current firing context is approaching budget. The cron session runs with a 200K-token context window on most models; soft-stop at **~140K tokens consumed** to leave headroom for the final scan, ledger edits, and run report.
   - You have read more than **~500 KB of filtered transcript content** across all sessions this firing.

   If budget is exhausted with work remaining, do NOT self-disable - the next firing picks up from the newest remaining entry.

5. **Otherwise loop.** Go back to step 3 and pull the next target. No re-scan between iterations - the `queue` list from step 2 is sufficient for this firing. (Re-running the script between iterations would burn context redundantly.)

6. **Re-scan and decide cron state.** Invoke the script one more time to verify the final state:

   ```bash
   clawstodian/scripts/scan-sessions.py > /tmp/clawstodian-sessions-capture-final.json
   ```

   If `queue` is empty → self-disable (see below). Otherwise → leave the cron enabled; next firing picks up.

7. **Write the run report** (see "Run report" below), then disable the cron if empty:

   ```bash
   ID=$(openclaw cron list --json | jq -r '.jobs[] | select(.name=="sessions-capture") | .id')
   openclaw cron disable "$ID"
   ```

   **Cron safety: disable means `openclaw cron disable`, NEVER `openclaw cron rm`.** Rm deletes the cron permanently.

## Unit-of-work procedure (one session)

Applied to each queue entry:

**1. Read the unread JSONL tail.** The entry's `transcript_path`, `lines_captured`, and `transcript_lines` fields tell you exactly what to read. Pick the lightest reading layer:

- **`sessions_history` tool** - cheapest for small, recent spans. Safety-filtered (caps at 80 KB, strips tool content by default). Use when the unread span is a few recent messages. Also the only option for sessions whose transcript file is missing from disk but whose registry row is still live (the `missing_transcripts` bucket).

- **Filtered JSONL tail via `jq`** - for larger unread spans. Reduces raw JSONL to user + assistant text only, typically 100-200x smaller than the raw bytes:

  ```bash
  tail -n +$((LINES_CAPTURED+1)) <transcript_path> | \
    jq -c 'select(.type=="message" and (.message.role=="user" or .message.role=="assistant")) | {ts: .timestamp, role: .message.role, content: (.message.content | if type == "string" then . else (map(select(.type=="text") | .text) | join("")) end | .[:2000])}' \
    > /tmp/clawstodian-sessions-capture-<sid-prefix>.jsonl
  ```

  Then `Read` the filtered file. Each line is one turn with timestamp, role, and text truncated to 2000 chars. Delete the temp file after processing.

- **Ad-hoc script in `/tmp/`** - only when the logic does not fit one jq pipe (joining two sessions' timelines, pre-computing bucket sizes, deduping against existing note sections). Write `/tmp/clawstodian-sessions-capture-<sid-prefix>.py`, invoke with `python3 /tmp/clawstodian-sessions-capture-<sid-prefix>.py`, clean up.

**2. Filter turns** per the rules below. The output is only human-facing user and assistant content:

- **System-injected user turns** - text starting with `[cron:`, `[heartbeat:`, `[hook:`, `System (`, `System:`, or `Conversation info` is gateway-generated, not operator-typed. Skip the turn and the assistant turn that follows.
- **Tool calls and tool results** - part of the model's work, not standalone content. Summarize inline (one short `-> read * grep * grep` style line) rather than pasting raw output. Omit lines with raw tool output exceeding a few hundred characters.

**3. Bucket by date.** For each surviving turn, convert timestamp to workspace-local date. Group into date buckets. A session's content may touch one date (common), two (midnight-crossing), or many (historical sessions).

**4. Apply per-date.** For each date bucket:

- If the date's note is `status: active` (or the file is missing): open or create the note, append a section with a descriptive header and `(~HH:MM UTC)` timestamp, content distilled per "What to Capture" in `memory/daily-note-structure.md`. Merge with existing sections on the same topic if an obvious match exists.
- If the date's note is `status: sealed`: do NOT mutate. Add the session id and date to the `bleed_over` accumulator for the run report.

**5. Merge slug siblings.** If today's date is in this session's buckets, check `memory/YYYY-MM-DD-*.md` for today, merge into the canonical note, delete the sibling. Ambiguous merges surface instead.

**6. Advance the ledger cursor.** Update the session's ledger entry per `memory/daily-note-structure.md` > "Session Ledger":

- New session (`status: new` in the queue): append a new H2 block at the end of `memory/session-ledger.md` with `kind`, `first_seen` (= now in ISO UTC), `last_activity` (= the row's `updatedAt` converted to ISO), `lines_captured` (= the transcript line count captured in step 1), `dates_touched`, `status` (`done` if the session's `updatedAt` is more than 7 days old, otherwise `active`).
- Existing session (`status: stale`): update `lines_captured`, `last_activity`, and `dates_touched` in place via narrow `Edit` calls. Do not reorder entries.

**7. Update daily-note frontmatter** on each touched note per `memory/daily-note-structure.md`: `last_updated`, `topics`, `people`, `projects`, `sessions` (append the session id's 8-char prefix if absent). Do not touch `para_status` here; it's set by `daily-seal`.

## Exec safety

- Run commands by exact path. No `eval`, `bash -c "..."`, or other indirection that hides the real command from the gateway's exec safety layer.
- **Always write multi-line script logic to `/tmp/clawstodian-sessions-capture-<context>.py` (or `.sh`) and invoke it by path. Do not use heredocs (`python3 <<EOF ... EOF`)** - some provider runtimes do not reliably block them, and the scripts become opaque to the operator reading the run transcript. A script on disk is also testable and reusable.
- `jq` and `python3 -c '<short expression>'` one-liners are fine when they fit on one line and the intent is obvious.
- Invoke `clawstodian/scripts/scan-sessions.py` by its workspace-relative path; do NOT absolutize or chain it through interpreter indirection.

## Worker discipline

- **Trust the script.** The queue it emits is authoritative. Do not re-enumerate `sessions_list` in the agent; do not run diagnostic scripts that cross-reference ledger vs disk. If the script gets something wrong, fix the script; do not duplicate its logic in the routine.
- Write daily-note updates FIRST, then advance the ledger cursor for that session. If either step fails, leave the cursor at its old position so the next firing retries.
- Never mutate a sealed daily note. Content for a sealed date goes into the `bleed_over` accumulator for the run report (per the program's approval-gate rule).
- Cursor edits to `memory/session-ledger.md` are narrow `Edit` calls on the matching lines, not full rewrites.
- PARA entity writes are not this routine's job. Durable insights that in-session agents did not file propagate to PARA later, when `para-extract` processes the sealed note.
- Cursor idempotency: if a cursor advance fails (note write succeeded but ledger edit failed, or vice versa), the next firing retries from the old cursor. The per-date merge rule makes any re-ingestion a no-op in terms of final note state.

## Run report

Two artifacts per meaningful firing: a full report on disk, and a multi-line scannable summary posted to the notifications channel. Every firing produces both.

### File on disk

Write to `memory/runs/sessions-capture/<YYYY-MM-DD>T<HH-MM-SS>Z.md`.

```markdown
# sessions-capture run report

- timestamp: 2026-04-19T12:30:00Z
- context: 2026-04-19T12:30Z firing
- outcome: captured
- cron_state: enabled → enabled

## Scan at firing start

- total_rows: 383 · unique_sessions: 377
- interactive: 14 · queue: 3 (new=1, stale=2)
- missing_transcripts: 16
- skipped: cron=36 · hook=0 · subagent=5 · dreaming=294 · empty=12

## Captures

- 96a0c068 (new): lines 0 → 189 · dates: [2026-04-19] · sections appended: 2 · slugs merged: 0 · bleed: 0
- cb89ae9b (stale): lines 130 → 214 · dates: [2026-04-17] · bleed: 1 (sealed note)
- 2da0badd (stale): lines 27 → 45 · dates: [2026-04-16] · bleed: 1 (sealed note)

## Bleed-over

- cb89ae9b → 2026-04-17 (sealed note)
- 2da0badd → 2026-04-16 (sealed note)

## Missing transcripts (unprocessed)

- 8c7c1630 / agent:main:main - transcript file absent on disk
- 626e5413 / agent:main:discord:channel:1490238855314673664 - same

## Queue after firing

- interactive: 14 · queue: 0 · missing_transcripts: 2
- cron state: enabled → disabled

## Commits

- (none - sessions-capture does not commit)

## Surfaced for operator

- 2 missing transcripts (see above) - live sessions whose JSONL file is gone; sessions_history fallback used where possible

## Channel summary

sessions-capture · 2026-04-19T12:30Z · captured
Captured: 3 sessions · dates: 2026-04-16, 2026-04-17, 2026-04-19
Bleed: 2 · slugs merged: 0
Missing transcripts: 2 (8c7c1630, 626e5413)
Queue: interactive=14 · pending=0 · cron: disabled
Report: memory/runs/sessions-capture/2026-04-19T12-30-00Z.md
```

### Channel summary

Multi-line, one insight per line:

**Meaningful firing** (some captures or surfaced items):

```
sessions-capture · <ISO UTC> · <outcome>
Captured: <N> sessions · dates: <list>
Bleed: <B> · slugs merged: <X>
Missing transcripts: <M>[ (<ids>)]
Queue: interactive=<I> · pending=<P> · cron: <enabled|disabled>
Report: memory/runs/sessions-capture/<ts>.md
```

`outcome` is one of: `captured` (processed interactive work), `disabled` (drained, cron self-disabled this firing), `no-op` (queue was empty - cron was enabled but nothing pending). Drop the `Missing transcripts` line when count is 0; drop the `Bleed` line when 0 and no captures happened this firing.

**Quiet firing** (queue empty at start, nothing to do):

```
sessions-capture · <ISO UTC> · no-op
Queue: interactive=<I> · pending=0 · cron: <enabled|disabled>
Report: memory/runs/sessions-capture/<ts>.md
```

### Every firing speaks

Every firing produces both a run-report file and a channel post - no silent firings. A quiet tick still announces so the operator sees the cron is alive. Report the state transition clearly when the cron self-disables: the post has `cron: disabled` and the outcome reflects the transition.
