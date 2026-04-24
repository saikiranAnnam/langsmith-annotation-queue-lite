# Architectural Decisions

---

## The Reservation Logic

When a reviewer requests the next available queue entry (`GET /entries/next`), the system has to ensure the same entry isn't handed out to two reviewers at once. This is the central concurrency problem in the whole system.

I evaluated three approaches:

**1. Application-Level Locking (Redis)**
Use Redis to set a lock before updating the database. The problem: if the server crashes mid-operation, the lock stays stuck and no one can claim that entry until it expires or is manually cleared. It also adds infrastructure that isn't needed for anything else.

**2. Optimistic Locking (version tracking)**
Each row has a version number. If two requests read the same version and both try to update, the second one fails and retries. Safe, but under any meaningful reviewer load, you get a lot of retries — requests constantly bumping into each other, which adds latency and wasted DB round trips.

**3. Database Row-Level Locking (`FOR UPDATE SKIP LOCKED`)**
The database finds the first available `pending` row and locks it for the duration of the transaction. Any concurrent request that tries to pick the same row sees the lock and skips to the next `pending` one instead. No retries, no external tools. The lock is held for ~5ms — just long enough to update the status — then released.

**Decision: Option 3.** It uses what the database is already good at. No extra infrastructure, no retry logic, correct behavior under concurrent load.

---

## Two different kinds of "lock"

One thing worth being explicit about: the database row lock and the `in_progress` status are two separate things.

- **Database lock (short-lived):** Held for ~5ms during the transaction. This is what prevents two reviewers from getting the same entry simultaneously. It releases the moment the transaction commits.
- **`in_progress` status (long-lived):** A logical state written to the DB. This persists for the duration of the review session — minutes or hours. Other requests see it and skip over entries in this state when looking for the next one.

These serve different purposes. The database lock handles concurrency. The status handles workflow state.

---

## TTL Recovery for Stuck Entries

If a reviewer's browser crashes mid-session, the database lock releases immediately (it's scoped to the transaction), but the `in_progress` status stays written to the DB. No other reviewer can pick up that entry.

**Solution: background task, not request-time check.**

A dedicated `asyncio` task (`requeue_stuck_entries_loop`) runs every 5 minutes and resets any `in_progress` entry where `reserved_at < NOW() - threshold` back to `pending`. The threshold is 30 minutes by default and is configurable via environment variable.

Why a background task and not a check on the next `GET /entries/next` request?

- Piggybacking TTL recovery on the reservation request adds unpredictable latency — you'd occasionally be running a cleanup sweep inline with serving a reviewer
- It needs a transaction-within-a-transaction pattern that's harder to reason about
- A separate task is independently observable and testable

**Why 30 minutes?** Reviewers working through complex traces might legitimately take 15-20 minutes on a single entry. An aggressive threshold (say, 5 minutes) would requeue active entries and create confusing double-review situations. 30 minutes is generous enough to cover real sessions while still handling crashes within a reasonable window.

**What happens to feedback on a requeued entry?** Feedback is not deleted on requeue. If a reviewer partially scored an entry and then crashed, their scores survive. The next reviewer who picks up that entry will see the partial annotations pre-filled in the sidebar.

The task is enabled/disabled via `settings.requeue_stuck_entries_enabled` — an operator can turn it off if needed without redeploying.

---

## Loading Existing Feedback

When a reviewer opens an entry that was partially annotated before, the rubric sidebar should show those existing scores. This is important for both the TTL recovery case (someone crashed mid-session) and for entries that get skipped and later revisited.

`GET /traces/{trace_id}/feedback` was already fully implemented in `services/traces.py`. It returns all feedback for a trace ordered by creation time. The frontend calls this in parallel with the entry fetch so both resolve before the UI renders — no sequential waterfall.

The decision here was simply: don't build a duplicate endpoint when one already exists and does exactly the right thing.

---

## Feedback: Upsert on (trace_id, key)

The `feedback` table has a `UNIQUE(trace_id, key)` constraint, and the batch insert uses `ON CONFLICT (trace_id, key) DO UPDATE SET ...`. This makes `POST /feedback/batch` behave as an upsert — first call creates the row, subsequent calls update it in place.

**Why this over frontend-managed routing?** The original approach had `useFeedbackManager` track whether a feedback ID existed and route to `POST` vs `PATCH` accordingly. That worked when the UI was the only caller, but any second client — a script, a direct API call, a different UI — could create duplicate rows. Moving enforcement to the DB means the backend is correct regardless of what's calling it.

The frontend is simpler as a result: `submitFeedback` always POSTs, no branching logic needed. `PATCH /feedback/:id` still exists for external callers who want to update a specific record by ID without knowing the trace+key pair.

One remaining edge case: if two reviewers annotate the same trace for the same key simultaneously, the last upsert wins. This is acceptable — queues are designed for single-reviewer workflows, and concurrent annotation of the same entry would be unusual.

---

## Span Storage: Three Columns

To support text highlighting within a JSON field, feedback stores three additional columns:

- `span_path JSONB` — path to the field, e.g. `["outputs", "answer"]`
- `span_start_index INTEGER` — character offset where the highlight starts
- `span_end_index INTEGER` — character offset where it ends

**Why JSONB for the path?** The path can contain both string keys (object properties) and integer indices (array positions). A `VARCHAR` would need parsing logic on read. `JSONB` stores it as a typed array and reads back directly.

**Why offsets, not a substring?** Storing the selected text itself would break if the trace content changes (e.g. re-ingested). Offsets are stable references into the string as it exists at annotation time. They also map directly to what `window.getSelection()` provides, so no translation is needed between what the browser captures and what gets stored.

**Single-field constraint:** Span selection is limited to within a single JSON string value. Cross-field selections are rejected with a warning. Supporting multi-field spans would require storing two full paths (anchor + focus) and more complex rendering logic — not worth the complexity for the current use case.
