# daily-notes

The workspace maintains one canonical daily note per calendar day at `memory/YYYY-MM-DD.md`, capturing activity, decisions, and context that happened that day. The note is the primary timeline record for the workspace.

## Primary mechanism: agents write notes in-session

The primary writer of daily notes is **the agent working in a session with the operator**. Per the workspace's `AGENTS.md` memory-maintenance rules, any agent doing notable work appends to `memory/YYYY-MM-DD.md` for that day as the work happens, commits, and pushes. This is the default path; it produces the highest-fidelity notes because the agent has full context of the conversation, the operator's intent, and the judgment calls made.

## Backstop mechanism: session-capture cron

Not every session ends cleanly. Agents forget, contexts get cut, sub-agent sessions and cron-kind sessions never touch the daily note at all, the gateway can be down, and a new clawstodian install lands on a workspace with history but no notes. The `capture-sessions` cron exists to close those gaps - not to be the primary writer.

The capture loop is **idempotent**: every session is discovered via `sessions_list`, classified once, and cursor-advanced forward through its JSONL tail. Content is bucketed by timestamp into the appropriate calendar date. Cursor-short-circuit skips any session whose `updatedAt` already matches the ledger's `last_activity`, so re-running the cron has near-zero cost when there is nothing new.

Content the agent already wrote into today's note in-session is merged by the "merge with existing sections on the same topic" rule during per-date application; the cron's reads advance the cursor past that content without duplicating it.

The cron is a **heartbeat-toggled burst**: it starts disabled, the heartbeat enables it when it detects gaps (un-admitted sessions or stale cursors), and it self-disables when the gaps drain. On a disciplined workspace it may go days without firing. On a fresh install over existing history it drains historical sessions in the background, one per firing, prioritized so live operator sessions are captured first.

## References

- Daily note format and frontmatter -> `memory/daily-note-structure.md`
- Session ledger format (cursor state) -> `~/clawstodian/docs/session-ledger.md` (package docs). The workspace file at `memory/session-ledger.md` is the state; the package doc is the format spec.
- PARA extraction program that reads sealed notes -> `clawstodian/programs/para.md`

Read `memory/daily-note-structure.md` before writing a daily note. Read `~/clawstodian/docs/session-ledger.md` before advancing cursors if you need to check field names or the H2-per-session shape.

## Prerequisites

- **Cross-session visibility.** OpenClaw's `sessions_list` defaults to tree-scoped visibility (a cron session sees only its own spawned children). This program requires `tools.sessions.visibility: "all"` in `~/.openclaw/openclaw.json` so cron-driven ticks can observe other sessions' transcripts. Without this, capture silently returns zero sessions and no daily-note content is ever produced. The install flow sets this; the `heartbeat` status sweep verifies it.
- **Transcript access from isolated sessions.** Cron routines in this program call `sessions_list`, optionally `sessions_history`, and `Read` against `transcriptPath`. All three must be permitted by the workspace's tool allowlist.

## Conventions

- **One canonical file per day.** The primary daily note is always `memory/YYYY-MM-DD.md`. Never two canonical files for the same date.
- **Slug siblings are transient.** Files like `memory/YYYY-MM-DD-<slug>.md` may appear during active sessions but must be merged into the canonical note. Sealed days never have slug siblings.
- **Lifecycle**:
  - `status: active` while the day is current and content is still arriving (today plus any past date not yet sealed).
  - `status: sealed` after editorial pass has finalized the day.
- **PARA handoff**:
  - `para_status: pending` set at seal time to queue the note for PARA extraction.
  - `para_status: done` set after PARA extraction completes.
- **Session ledger is authoritative for capture state.** `memory/session-ledger.md` records which sessions have been classified and how far their transcripts have been read. Daily notes reference sessions by id only; cursor state does NOT live in daily-note frontmatter.
- **Sources of truth**: raw JSONL at `transcriptPath` from `sessions_list` (authoritative, complete), `sessions_history` (safety-filtered view, useful when raw JSONL reads are blocked), `git log`, workspace diffs, the agent's own observations.

## Authority

- Create and edit `memory/YYYY-MM-DD.md` for any date that is today or unsealed past.
- Merge and delete `memory/YYYY-MM-DD-<slug>.md` siblings into the canonical file.
- Read session transcripts via `sessions_list`, `sessions_history`, and raw JSONL via `transcriptPath`.
- Create and update entries in `memory/session-ledger.md`.
- Flip lifecycle markers on past-day notes (`status: active -> sealed`, `para_status: pending`).
- Update frontmatter fields defined in `memory/daily-note-structure.md`.
- File clearly durable insights surfaced during a pass into obvious PARA locations (`resources/<descriptive-slug>.md`, `projects/<name>/README.md` when the insight is scoped to a project). Ambiguous filings surface for operator decision.

Must NOT rewrite sealed notes cosmetically or for stylistic reasons. Must NOT write into a sealed note; content intended for a sealed date surfaces as a `bleed-over` anomaly in the run report.

## Approval gates

- **Obvious placement -> act.** Appending today's session activity to today's note, merging an obvious slug sibling, filing an insight into a clearly-right location.
- **Ambiguous placement -> surface.** An insight that could live in multiple PARA buckets, a slug sibling whose content conflicts with the canonical note, a new top-level folder. In-session: ask the operator. Via cron dispatch: include in the run report so the operator sees it in the logs channel.
- **Past-date content arriving after seal -> surface, do not apply.** If a session's newly-captured JSONL contains entries timestamped for a date whose note is already `sealed`, do not modify the sealed note. Surface the bleed as an anomaly. The operator decides whether to reopen the seal.
- **Material rewrite of a sealed note -> ask.** Only allowed with explicit operator approval.

## Escalation

- If `sessions_list` returns zero rows and the visibility config appears correct, surface the discrepancy and stop. This is the silent-failure mode the prerequisite exists to prevent; treat zero rows with known-good config as a signal something upstream is broken.
- If a ledger entry's `lines_captured` exceeds the current transcript line count, the transcript was truncated or rotated. Surface and leave the ledger entry alone (operator decides whether to reset).
- If a slug sibling's content conflicts materially with the canonical note, surface the conflict and leave both files untouched until the operator resolves.
- If the target note is unreadable, corrupted, or in an unexpected encoding, surface and stop.

## Session classification

Every session observed by this program is classified exactly once and the result is stored in `memory/session-ledger.md`. Classification rules:

- `kind: cron` -> `skipped`, reason: "cron session". Cron-dispatched routines land here; their activity is not part of the human daily note.
- `kind: hook` -> `skipped`, reason: "hook session".
- `kind: node` (sub-agent) where `parentSessionKey` points to a session already classified `interactive` -> `skipped`, reason: "sub-agent of <parent id>". The parent session's transcript contains the sub-agent's user-visible output.
- Session with zero user-authored messages -> `skipped`, reason: "delivery-only session". These are outbound-only sessions with no interactive content.
- Everything else (`main`, `group`, `other` with user messages) -> `interactive`.

Classification is idempotent. A session classified as `skipped` is never re-examined except to confirm the reason on demand.

### Turn-level filtering within an interactive session

An `interactive` classification means the session as a whole carries human content, not that every turn in its transcript does. When extracting content from the JSONL, filter turn-by-turn:

- **Cron-injected user turns** have a literal prefix `[cron:<jobId> <jobName>]` at the start of the `content` field. OpenClaw emits this consistently for cron-triggered turns; treat any user turn whose content starts with `[cron:` as non-human and skip it along with the assistant turn that follows.
- **Heartbeat-injected user turns** in the main session have NO structural marker in the JSONL - the gateway appends them as regular user messages. Detect by content: a user turn whose content matches (exactly or with only a whitespace / timestamp trailing line difference) one of the `tasks[].prompt` strings in the workspace's `HEARTBEAT.md` is a heartbeat tick, not an operator message. Skip it and its assistant response. If the operator has customized `HEARTBEAT.md`, read it fresh each tick so the filter stays in sync.
- **Hook-injected user turns** (webhook / Gmail / HTTP hook) also have no structural marker. If the workspace uses hooks, their payload shape is known to the operator; treat such turns as "what the integration said" rather than operator speech. If hooks are not configured, this case does not arise.
- **Tool calls and tool results** within an assistant turn are part of the model's work, not standalone content. Summarize them inline (one short `-> read * grep * grep` style line in the daily-note section) rather than pasting tool output verbatim. Lines with raw tool output exceeding a few hundred characters should be omitted entirely.

The filter output is what lands in the daily note. Everything else stays in the JSONL but does not appear in the human timeline.

## Behaviors

### Capture one session's new content

Dispatched by the `capture-sessions` routine. This behavior describes the unit of work for **one session**: enumerate gaps, pick a target, classify if new, read its unread JSONL span, bucket by date, apply per-date, advance the ledger cursor. The routine owns the per-firing strategy (how many units, in what order, with what budget caps); see `clawstodian/routines/capture-sessions.md` for the Phase 1 / Phase 2 batching rules. This section defines what happens for each unit.

The single unit covers every case: a brand-new operator session that just appeared, an active session whose cursor fell behind during a gateway outage, a historical session from before the install was ever done. The only differences are which session is selected and how many JSONL lines get read for this unit; the apply-logic is identical.

1. **Enumerate gaps.** Read `memory/session-ledger.md`. Call `sessions_list({limit: 500})`. For each sessions_list row, determine its gap state:
   - **un-admitted** - row is in sessions_list but has no ledger entry.
   - **stale** - row is in sessions_list, ledger entry exists, and `row.updatedAt > ledger.last_activity`.
   - **current** - row is in sessions_list, ledger entry exists, `row.updatedAt == ledger.last_activity` (no work).
   - **skipped** - ledger entry with `classification: skipped` (no work).

2. **Select target.** Pick one gap to process as this unit of work. The routine's calling strategy decides which: typically the newest-`updatedAt` un-admitted or stale session on a given invocation, so live sessions capture before historical drain.

3. **Classify if new.** For an `un-admitted` target, apply the classification rules. Append a ledger entry. If classification is `skipped`, this unit is done - no JSONL read, no daily-note write. The routine may continue to the next unit.

4. **Read JSONL tail, filtered.** Raw `Read` of a session transcript can blow context on active sessions: tool results and tool calls dominate transcript bytes (empirically ~88% in a large active session; user+assistant text is often under 3%). Pick the lightest reading layer that covers the unread span:

   - **`sessions_history`** - cheapest for recent small spans. Safety-filtered (caps at 80 KB, strips tool content by default). Use when the unread span is a handful of recent messages and fidelity beyond the 80 KB cap is not needed.
   - **Inline `jq` filter piped to `/tmp/`** - for larger unread spans. Reduces the JSONL tail to user + assistant text only, typically 100-200x smaller than the raw span:
     ```bash
     tail -n +$((lines_captured+1)) <transcriptPath> | \
       jq -c 'select(.type=="message" and (.message.role=="user" or .message.role=="assistant")) | {ts: .timestamp, role: .message.role, content: (.message.content | if type == "string" then . else (map(select(.type=="text") | .text) | join("")) end | .[:2000])}' \
       > /tmp/clawstodian-capture-<sid-prefix>.jsonl
     ```
     Then `Read` `/tmp/clawstodian-capture-<sid-prefix>.jsonl`. Each line is one filtered turn with timestamp, role, and text truncated to 2000 chars. Delete the temp file after processing.
   - **Ad-hoc script in `/tmp/`** - only when the logic does not fit one jq pipe (joining two sessions' timelines, pre-computing bucket sizes, deduping against existing note sections). Write `/tmp/clawstodian-capture-<sid-prefix>.py`, invoke with `python3 /tmp/clawstodian-capture-<sid-prefix>.py`, read stdout or a result file, clean up.

   Whichever layer is used, parse the output turn-by-turn. Record the source transcript's line count at time of read (`wc -l < <transcriptPath>`); that becomes the new `lines_captured` in step 9.

5. **Filter turns.** Apply the turn-level filter rules above: skip cron-prefixed user turns and their assistant responses, skip heartbeat-matched user turns and their responses, skip hook payload turns, summarize tool calls inline rather than pasting raw output.

6. **Bucket by date.** For each surviving `role: "user"` or `role: "assistant"` entry, convert its timestamp to the workspace-local date. Group entries into date buckets. A session's content may touch one date (the common case), two (midnight-crossing), or many (historical sessions spanning weeks).

7. **Apply per-date.** For each date bucket:
   - If the date's note is `status: active` (or missing): open or create the note, append a section with a descriptive header and `(~HH:MM UTC)` timestamp, content distilled per the "What to Capture" rules in `memory/daily-note-structure.md`. Merge with existing sections on the same topic if an obvious match exists. This is where content the agent already wrote in-session gets absorbed rather than duplicated.
   - If the date's note is `status: sealed`: do NOT mutate the note. Add the session id and date to a `bleed_over` accumulator for the run report. Common and expected on historical backfill (most historical sessions will only touch already-sealed dates); unusual and worth attention during steady-state capture.

8. **Merge slug siblings.** If the target session's bucket includes today's date, check `memory/YYYY-MM-DD-*.md` for today. Read, merge into the canonical note under an appropriate section, delete the sibling file. Ambiguous merges surface instead.

9. **File obvious durable insights.** If a decision, resolved bug, or reusable pattern clearly belongs in `resources/` or a project's `README.md`, file it now. Ambiguous insights surface instead.

10. **Advance the ledger cursor.** Update `lines_captured` to the source transcript's line count at time of read (captured in step 4), `last_activity` to the row's `updatedAt`, and extend `dates_touched` with any newly-affected dates. Edit in place via narrow `Edit` calls; never rewrite the whole ledger. For a newly-admitted session, set `status`: `done` if the session's `updatedAt` is more than 7 days old, otherwise `active`.

11. **Update frontmatter** on each touched daily note per `memory/daily-note-structure.md`: `last_updated`, `topics`, `people`, `projects`, `sessions` (append the session id's 8-char prefix if not present), and `para_status` handling per the structure spec.

12. **Return to the caller.** This unit of work is complete. The routine decides whether to process another unit in the same firing or end the firing.

If a cursor advance fails (note write succeeded but ledger edit failed, or vice versa), the next firing retries from the old cursor. The worst case is re-ingesting some of the same content; the per-date "merge with existing sections on same topic" rule makes that a no-op in terms of final note state. Cursor idempotency is what makes the whole loop safe to re-run.

### Seal a past-day note

Close and finalize one unsealed past-day note with disk-fidelity.

**Target selection** (for cron-driven sealing of the oldest unsealed note):

1. List `memory/YYYY-MM-DD.md` files where the date is before today (workspace local timezone).
2. Candidate = frontmatter `status: active`, OR the file is missing for a past date where `git log --since=YYYY-MM-DD --until=YYYY-MM-DD+1d` shows commits.
3. **Midnight grace.** Reject any candidate whose date is yesterday if the current workspace-local time is less than 2 hours past midnight. A session whose activity straddles midnight needs at least one more `daily-note` firing to have its post-midnight content captured into today's note and any pre-midnight content captured into yesterday's note; sealing yesterday before that finishes creates a race that sends late-captured content into the `bleed_over` accumulator instead of into yesterday's note. Only yesterday is affected; older past-days have no live sessions and no straddling risk.
4. Pick the **oldest** remaining candidate.

**Trivial-day fast-path.** Before the full seal, inspect the note body (excluding frontmatter). If **<=2 sections and <=1KB body**:

- Standardize frontmatter per `memory/daily-note-structure.md`.
- Write a 1-2 sentence day summary if missing.
- Flip `status: active` -> `status: sealed`.
- Leave or set `para_status: pending`.
- Update `last_updated`.
- Commit.

Skip the merge and organize steps. This prevents expensive compute on "quiet day - no user interactions" notes.

**Full seal.**

1. **Merge topic-suffixed variants.** Check for `memory/YYYY-MM-DD-*.md`. Read, merge into canonical, delete the variants. If none, skip.
2. **Read the full daily note** and understand it before changing anything.
3. **Gather authoritative inputs:**
   - Raw session JSONL from disk for that date (authoritative record; `sessions_history` returns a safety-filtered view).
   - `git log --since --until` for that date.
   - `git diff` summaries for touched files.
4. **Organize the note:**
   - Chronological order (by UTC timestamp).
   - Merge duplicate sections covering the same topic.
   - Every `##` header must be descriptive and searchable. Include topic name + what happened + `(~HH:MM UTC)` timestamp.
   - Write a 2-3 sentence day summary after the `# YYYY-MM-DD` heading: what was this day about?
5. **Remove noise.** Daily notes capture what *happened*, not which automations ran. Remove heartbeat digest output with no user interaction, tick status sections, cron-run dumps unless they led to decisions or discussion.
6. **Curate frontmatter** per `memory/daily-note-structure.md`. Judgment calls:
   - `people` - remove-the-name test: if I remove this name, does the day's story change? Exclude internet strangers, bystanders, names in cron reminders.
   - `projects` - same test. Include implicit work. Exclude projects mentioned only in file paths.
   - `topics` - 3-8 specific phrases. The day's themes, not a section-by-section list.
7. **Thread continuity.** When a section clearly continues work from a previous day, add `(continued from YYYY-MM-DD)` in the section body. Only when the continuation is unambiguous.
8. **Flip `status: active` -> `status: sealed`.** Leave or set `para_status: pending`. Update `last_updated` to the current ISO timestamp.

Do not perform PARA extraction here. That responsibility belongs to `clawstodian/programs/para.md`.

**Commit.** Add only the files you changed, never `git add -A` or `git add .`. Commit message: `memory: seal YYYY-MM-DD - <topic summary>`. Push immediately.

## What NOT to do

- Do not create `memory/YYYY-MM-DD-<slug>.md` new files; merge any that exist into the canonical note.
- Do not reconstruct content for days with no evidence.
- Do not rewrite sealed notes cosmetically.
- Do not write into a sealed note at all; surface bleed-over instead.
- Do not re-read session transcripts from line 0 if the ledger has a cursor; advance from the cursor. (Re-reading from 0 is only correct when the ledger has no entry for that session, i.e. first admission.)
- Do not store cursor state in daily-note frontmatter; the ledger is authoritative.
- Do not delete ledger entries to match observed state (e.g. if a transcript disappears); surface the anomaly and leave the entry.
- Do not perform PARA extraction as part of tending or sealing.
- Do not auto-create new top-level directories for insight filing.
- Do not create stub PARA entities.
- Do not batch multiple past-day seals in one pass; the seal behavior is strictly one note per invocation.
- Do not treat the `capture-sessions` cron as the primary writer of daily notes. Agents in session are the primary writers; the cron is the backstop.
- Do not conflate the program's unit of work with the routine's per-firing strategy. The program's capture behavior describes one session's content; the routine decides how many sessions per firing.
