# capture-sessions (routine)

Backstop for the daily-notes program. Admits new sessions to `memory/session-ledger.md` and drains interactive capture gaps into the appropriate daily note(s) - catching what in-session agents did not finalize themselves.

## Program

`clawstodian/programs/daily-notes.md` - follow its conventions, authority, approval gates, escalation rules, and what-NOT-to-do constraints. The program defines the workspace's convention for daily notes; this routine describes the cron's procedure for capturing session content into them.

See `memory/daily-note-structure.md` for the session-ledger format (field definitions, update rules) and the daily-note format.

## Target

All capture gaps in `sessions_list` vs. `memory/session-ledger.md`:

- **un-admitted**: present in `sessions_list` but absent from the ledger.
- **stale**: ledger entry exists, but `sessions_list` row's `updatedAt > ledger.last_activity`.

Within each kind, prioritize by newest `updatedAt` so live sessions capture before historical drain.

## Classification

Every session observed by this routine is classified exactly once and the result is stored in the ledger:

- `kind: cron` -> `skipped`, reason: "cron session". Cron-dispatched routines land here.
- `kind: hook` -> `skipped`, reason: "hook session".
- `kind: node` (sub-agent) where `parentSessionKey` points to a session already `interactive` -> `skipped`, reason: "sub-agent of <parent id>". The parent's transcript contains the sub-agent's user-visible output.
- Session with zero user-authored messages -> `skipped`, reason: "delivery-only session".
- Everything else (`main`, `group`, `other` with user messages) -> `interactive`.

Classification is idempotent. Once `skipped`, a session is not re-examined except to confirm the reason on demand.

## Turn-level filtering inside an interactive session

An `interactive` classification means the session carries human content overall, not that every turn does. When reading the JSONL, filter turn-by-turn:

- **Cron-injected user turns** - literal prefix `[cron:<jobId> <jobName>]` at the start of `content`. Skip the turn and the assistant turn that follows.
- **Heartbeat-injected user turns** (in main sessions) - no structural marker. Detect by content: if a user turn matches (exactly or with only trailing whitespace / timestamp differences) one of the `tasks[].prompt` strings in the workspace's `HEARTBEAT.md`, treat it as a heartbeat tick and skip it plus its assistant response. Read `HEARTBEAT.md` fresh each firing so the filter stays in sync with operator edits.
- **Hook-injected user turns** (webhook / Gmail / HTTP) - no structural marker. If the workspace uses hooks, the payload shape is known to the operator; treat those turns as "what the integration said" rather than operator speech. Skip if hooks are not configured.
- **Tool calls and tool results** - part of the model's work, not standalone content. Summarize inline (one short `-> read * grep * grep` style line) rather than pasting raw output. Omit lines with raw tool output exceeding a few hundred characters.

The filter output is what lands in the daily note. Everything else stays in the JSONL but does not appear in the human timeline.

## Exec safety

- Run commands by exact path. No `eval`, `bash -c "..."`, or other indirection that hides the real command from the gateway's exec safety layer.
- For multi-line script logic, write the script to `/tmp/clawstodian-capture-<context>.py` (or `.sh`) and invoke it by path. Do not inline code via heredoc to an interpreter (`python3 <<EOF ... EOF`); the safety layer blocks that as obfuscation.
- `jq` and `python3 -c '<short expression>'` one-liners are fine when they fit on one line and the intent is obvious.

## Worker discipline

Two phases per firing.

**Phase 1 - admit all un-admitted sessions.** Classification is cheap (check `kind`, look for user messages). For every session in `sessions_list` with no ledger entry, classify and append an entry. No per-firing cap on Phase 1: if there are 40 un-admitted cron sessions, admit all 40. A single append of multiple H2 blocks at the end of the ledger is fine; narrow per-line edits are unnecessary for brand-new entries. Skipped admissions get `classification: skipped` and a short `reason`; interactive admissions get `classification: interactive` with `lines_captured: 0` and await Phase 2 for their first read.

**Phase 2 - process interactive gaps, bounded.** Enumerate interactive gaps (both the `lines_captured: 0` admissions from Phase 1 AND pre-existing stale-cursor entries). Sort by `updatedAt` descending. Process one at a time per the unit-of-work procedure below. Continue to the next-newest gap until ANY of these hold:

- No interactive gaps remain.
- The firing is approaching its budget. The cron session runs with a ~200K-token context window and compaction kicks in around 160-180K; target a soft stop at **~140K tokens of consumed context** to leave headroom for the self-disable check and run report. In JSONL terms, that roughly corresponds to **~500 KB of filtered content** read across all sessions processed this firing (each filtered session is typically 20-100 KB).
- Five interactive sessions have been processed this firing (hard cap to prevent runaway on pathological queues).

If Phase 2 runs out of budget with interactive gaps still remaining, the cron stays enabled and the next firing picks up from the newest remaining gap.

**Discipline across phases:**

- Read JSONL with `Read` from `lines_captured + 1`, or from offset 0 for a newly-admitted interactive session. Do not re-read from 0 when the ledger has a cursor.
- Write daily-note updates FIRST, then advance the ledger cursor for that session. If either step fails, leave the cursor at its old position so the next firing retries.
- Never mutate a sealed daily note. Content for a sealed date goes into the `bleed_over` accumulator for the run report (per the program's approval-gate rule).
- Cursor edits to `memory/session-ledger.md` are narrow `Edit` calls on the matching lines, not full rewrites.

## Unit-of-work procedure (one session)

Applied to each interactive gap selected in Phase 2:

1. **Read JSONL tail, filtered.** Raw `Read` of a session transcript can blow context: tool results and tool calls dominate transcript bytes (empirically ~88% in a large active session; user+assistant text is often under 3%). Pick the lightest reading layer that covers the unread span:

   - **`sessions_history` tool** - cheapest for recent small spans. Safety-filtered (caps at 80 KB, strips tool content by default). Use when the unread span is a handful of recent messages and fidelity beyond the 80 KB cap is not needed.
   - **Inline `jq` filter piped to `/tmp/`** - for larger unread spans. Reduces the JSONL tail to user + assistant text only, typically 100-200x smaller than the raw span:
     ```bash
     tail -n +$((lines_captured+1)) <transcriptPath> | \
       jq -c 'select(.type=="message" and (.message.role=="user" or .message.role=="assistant")) | {ts: .timestamp, role: .message.role, content: (.message.content | if type == "string" then . else (map(select(.type=="text") | .text) | join("")) end | .[:2000])}' \
       > /tmp/clawstodian-capture-<sid-prefix>.jsonl
     ```
     Then `Read` the filtered file. Each line is one turn with timestamp, role, and text truncated to 2000 chars. Delete the temp file after processing.
   - **Ad-hoc script in `/tmp/`** - only when the logic does not fit one jq pipe (joining two sessions' timelines, pre-computing bucket sizes, deduping against existing note sections). Write `/tmp/clawstodian-capture-<sid-prefix>.py`, invoke with `python3 /tmp/clawstodian-capture-<sid-prefix>.py`, clean up.

   Record the source transcript's line count at time of read (`wc -l < <transcriptPath>`); that becomes the new `lines_captured` after step 6.

2. **Filter turns** per the classification and turn-level filtering rules above. The output is only human-facing user and assistant content.

3. **Bucket by date.** For each surviving entry, convert its timestamp to the workspace-local date. Group into date buckets. A session's content may touch one date (common), two (midnight-crossing), or many (historical sessions).

4. **Apply per-date.** For each date bucket:
   - If the date's note is `status: active` (or missing): open or create the note, append a section with a descriptive header and `(~HH:MM UTC)` timestamp, content distilled per the "What to Capture" rules in `memory/daily-note-structure.md`. Merge with existing sections on the same topic if an obvious match exists. This is where content the agent already wrote in-session gets absorbed rather than duplicated.
   - If the date's note is `status: sealed`: do NOT mutate. Add the session id and date to a `bleed_over` accumulator for the run report.

5. **Merge slug siblings.** If today's date is in this session's buckets, check `memory/YYYY-MM-DD-*.md` for today, merge into the canonical note, delete the sibling. Ambiguous merges surface instead.

6. **File obvious durable insights.** Clear decisions / resolved bugs / reusable patterns that belong in `resources/` or a project's `README.md` - file now. Ambiguous insights surface.

7. **Advance the ledger cursor.** Update `lines_captured` to the line count captured in step 1, `last_activity` to the row's `updatedAt`, extend `dates_touched`. For a newly-admitted session, set `status`: `done` if the session's `updatedAt` is more than 7 days old, otherwise `active`.

8. **Update daily-note frontmatter** on each touched note per `memory/daily-note-structure.md`: `last_updated`, `topics`, `people`, `projects`, `sessions` (append the session id's 8-char prefix if absent), `para_status` per the structure spec.

Cursor idempotency: if a cursor advance fails (note write succeeded but ledger edit failed, or vice versa), the next firing retries from the old cursor. The per-date merge rule makes any re-ingestion a no-op in terms of final note state.

## Self-disable on empty queue

After Phase 2 returns, re-count un-admitted and stale-cursor sessions. If both are zero, disable the cron:

```bash
openclaw cron disable capture-sessions
```

**Cron safety: disable means `openclaw cron disable`, NEVER `openclaw cron remove`.** Remove deletes the cron permanently.

## Run report

Two artifacts per meaningful firing: a full report written to disk and a single-line summary delivered to the notifications channel. The operator sees the scannable summary in the channel and can drill into the file when they want detail.

### File on disk

Write to `memory/runs/capture-sessions/<YYYY-MM-DD>T<HH-MM-SS>Z.md` (UTC, colons replaced with hyphens so the filename is filesystem-safe and sorts chronologically).

File shape:

```markdown
# capture-sessions run report

- timestamp: 2026-04-18T12:30:00Z
- cron_state_before: enabled
- cron_state_after: enabled

## Phase 1 - admissions

- admitted: 3
  - 96a0c068 -> interactive (kind: main)
  - 5f12bbdd -> skipped (kind: cron, reason: cron session)
  - 7c83eeaa -> skipped (kind: cron, reason: cron session)

## Phase 2 - captures

- processed: 1
  - 96a0c068: lines 142 -> 189 | dates: [2026-04-18] | sections appended: 2 | slugs merged: 0 | insights filed: 0 | bleed: 0

## Bleed-over (if any)

- (none)

## Queue after firing

- un-admitted: 0
- stale: 0

## Channel summary

capture-sessions: admitted 3 (skipped=2, interactive=1) | captured 1 | dates [2026-04-18] | bleed 0 | queue: u=0/s=0 | cron: enabled | report: memory/runs/capture-sessions/2026-04-18T12-30-00Z.md
```

Keep each section tight. The file exists for post-mortem, not for narrative. Skip writing the file entirely on NO_REPLY firings (see below).

### Channel summary

Single line the cron runner delivers to the notifications channel:

```
capture-sessions: admitted <N> (skipped=<s>, interactive=<i>) | captured <M> | dates [YYYY-MM-DD, ...] | bleed <Z> | queue: u=<u>/s=<s2> | cron: <enabled|disabled> | report: memory/runs/capture-sessions/<ts>.md
```

- `admitted` - total ledger entries added this firing; `skipped` + `interactive` sum to it.
- `captured` - interactive sessions whose cursor advanced (includes Phase 1 admissions that got a Phase 2 first-read).
- `bleed` - count of sessions whose new content touched a sealed-date note. Detail lives in the file.
- `queue: u=/s=` - un-admitted / stale counts remaining; drives the heartbeat's next toggle decision.
- `report: ...` - relative path to the file so the operator can open it with one step.

### NO_REPLY

Return `NO_REPLY` (no channel post, no file on disk) when `admitted` is 0 OR all admissions were `skipped`, AND `captured` is 0, AND the cron state did not change. A no-op firing produces no artifacts.

Always report (file + channel) when: any interactive capture happened (`captured > 0`), any bleed surfaced (`bleed > 0`), or the cron self-disabled (state transition).
