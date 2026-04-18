# daily-notes

The workspace maintains one canonical daily note per calendar day at `memory/YYYY-MM-DD.md`, capturing activity, decisions, and context that happened that day. The note is the primary timeline record for the workspace.

Daily notes are fed by an **idempotent capture loop** over OpenClaw's session transcripts. Every session is discovered via `sessions_list`, classified once, and then cursor-advanced forward: each tick reads only the JSONL lines that are new since the prior run and buckets content by timestamp into the appropriate date. No re-scanning, no re-processing, no fuzzy text deduplication.

The loop is split across two routines: `daily-note` handles the steady state (sessions active in the last six hours) and `backfill-sessions` drains the historical queue (sessions older than that window with no ledger entry). The six-hour window is wider than the strict "recent activity" span on purpose: it absorbs gateway downtime up to ~6h without creating a silent capture gap, at near-zero extra cost because cursor-short-circuit skips any session whose `updatedAt` already matches the ledger's `last_activity`.

## References

- Daily note format and frontmatter -> `memory/daily-note-structure.md`
- Session ledger format (cursor state) -> `memory/session-ledger.md`
- PARA extraction program that reads sealed notes -> `clawstodian/programs/para.md`

Read `memory/daily-note-structure.md` before writing a daily note. Read `memory/session-ledger.md` before advancing cursors.

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

### Ingest recent activity

Steady-state capture of the last ~6 hours of session activity into today's note (and, when bleed-over lands, yesterday's if still active).

1. **Discover active sessions.** Call `sessions_list({activeMinutes: 360, limit: 500})`. Result is sessions with `updatedAt` within the last 6 hours. The window is deliberately wider than the 30-minute cron cadence so that a gateway restart or scheduler hiccup up to ~6h does not create a silent capture gap.
2. **Classify new sessions.** For each row not already in `memory/session-ledger.md`: classify per the rules above, append an entry to the ledger. If classification is `skipped`, stop for that session.
3. **Short-circuit unchanged sessions.** For each `interactive` entry whose ledger `last_activity` equals the row's `updatedAt`: skip. No new lines, no work.
4. **Read new JSONL tail.** For each session needing work, open `transcriptPath` with `Read` starting at `offset: lines_captured + 1`. Parse each returned line as JSON.
5. **Bucket by date.** For each JSONL entry with `role: "user"` or `role: "assistant"`, convert its timestamp to the workspace-local date. Group entries into date buckets. One session's new lines may touch one, two, or occasionally more dates (mostly the current day, sometimes the prior day if capture crossed midnight).
6. **Apply per-date.** For each date bucket:
   - If the date's note is `status: active` (or missing): open or create the note, append a section with a descriptive header and `(~HH:MM UTC)` timestamp, content distilled per the "What to Capture" rules in `memory/daily-note-structure.md`. Merge with existing sections on the same topic if an obvious match exists.
   - If the date's note is `status: sealed`: do NOT mutate the note. Add the session id and date to a `bleed_over` accumulator for the run report.
7. **Merge slug siblings.** After applying today's bucket, check `memory/YYYY-MM-DD-*.md` for today. Read, merge into canonical note under an appropriate section, delete the sibling file. Ambiguous merges surface instead.
8. **File obvious durable insights inline.** If a decision, resolved bug, or reusable pattern clearly belongs in `resources/` or a project's `README.md`, file it now. Ambiguous insights surface instead.
9. **Advance the ledger cursor.** For each session processed successfully: update `lines_captured` to the new line count, update `last_activity` to the row's `updatedAt`, extend `dates_touched` with any newly-affected dates. Edit in place via narrow `Edit` calls; never rewrite the whole ledger.
10. **Update frontmatter** on each touched daily note per `memory/daily-note-structure.md`: `last_updated`, `topics`, `people`, `projects`, `sessions` (append the session id's 8-char prefix if not present), and `para_status` handling per the structure spec.

If a session's cursor advance fails (note write succeeded but ledger edit failed, or vice versa), the next tick retries from the old cursor. The worst case is re-ingesting some of the same content; the `Extract from JSONL tail` step is idempotent by timestamp bucket merge, so duplicates consolidate rather than accumulate.

### Ingest a historical session

Full-transcript capture of one session that has no ledger entry and was NOT surfaced by the recent-activity window. Used by the `backfill-sessions` burst worker during initial install on an already-populated workspace and to catch sessions that slipped past the 6-hour window.

1. **Select target.** Read `memory/session-ledger.md`. Call `sessions_list({limit: 500})` (no `activeMinutes` filter). Pick the **oldest session by `updatedAt`** that is NOT present in the ledger.
2. **Classify.** Apply the classification rules. If `skipped`, append the `skipped` ledger entry and stop.
3. **Read the full transcript.** Open `transcriptPath` with `Read`. Parse every line.
4. **Bucket by date.** Same as step 5 in "Ingest recent activity": group entries by workspace-local date of their timestamp.
5. **Apply per-date.** Same as step 6. Most historical sessions touch only sealed dates; those buckets go to the `bleed_over` accumulator. If the operator wants to retroactively surface that content, they must reopen the seal; this program never does so unbidden. A historical session may also touch an `active` past date (recent days not yet sealed), in which case content is applied normally.
6. **Append the ledger entry.** Create the `interactive` entry with final `lines_captured`, `dates_touched`, `last_activity`, and `status` (`done` if the session's `updatedAt` is older than 7 days, otherwise `active`).
7. **One session per firing.** Do not loop to the next historical session. The burst worker re-fires on its schedule until the ledger is caught up.

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
- Do not re-read session transcripts from line 0 if the ledger has a cursor; advance from the cursor.
- Do not store cursor state in daily-note frontmatter; the ledger is authoritative.
- Do not delete ledger entries to match observed state (e.g. if a transcript disappears); surface the anomaly and leave the entry.
- Do not perform PARA extraction as part of tending or sealing.
- Do not auto-create new top-level directories for insight filing.
- Do not create stub PARA entities.
- Do not batch multiple past-day seals in one pass; one note per invocation.
- Do not loop in a single firing. Each behavior processes one unit of work (one session's new lines for tending; one historical session for backfill; one past-day note for sealing) and returns.
