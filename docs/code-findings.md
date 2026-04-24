# Pre-coding Findings

Notes i have written from reading the starter code before writing anything. These are the bugs and gaps I found that needed fixing — documented here so the fixes in the implementation have context.

---

## Backend gaps in the starter

**`complete_entry` returns 204 with no body**
The router had `status_code=204` and `response_model=None`. The existing tests expected `200` with a `{"message": ...}` body. Fixed: changed to `status_code=200` and returned a message dict.

**Empty queue message mismatch**
The router returned `"Queue is empty"` but the tests asserted `"No pending entries in queue"`. Fixed: aligned the router message to match the tests.

---

## Schema gaps

**No `reserved_at` / `reserved_by` on `queue_entries`**
Needed for the TTL recovery job and for attribution. Added in migration.

**No span columns on `feedback`**
`span_path`, `span_start_index`, `span_end_index` were referenced in `types.ts` and the test file but didn't exist in the DB or Pydantic schemas. Added in migration and schemas.

---

## Frontend gaps

The starter had basically no frontend for the annotation flow — just an empty `AnnotationQueuePage` stub and no hooks. Everything in `client/src/hooks/` and most of `client/src/components/` is new.

The existing `useApi.ts` had `useCompleteQueueEntry` with a hardcoded static SWR key (`"complete-entry"`) that would break if you called it from multiple places. Updated the key to something scoped.

---

## Tests that needed fixing

From `test_queues.py`:
- `test_get_next_entry`: asserted `status == "pending"` — should be `"in_progress"` after reservation
- `test_get_next_entry_empty_queue`: wrong message string (see above)
- `test_complete_entry`: expected 204, needed to change to 200

From `test_feedback.py`:
- `test_get_feedback`, `test_get_feedback_not_found`, `test_delete_feedback`: all failed because `GET /feedback/{id}` didn't exist

Everything else in the test suite passed without changes.
