# LangSmith Annotation Queue Lite — Solution

---

## Table of Contents

- [TL;DR](#tldr)
- [Key Highlights](#key-highlights)
- [Problem](#problem)
- [What I Added vs Starter Code](#what-i-added-vs-the-starter-code)
- [Architecture](#architecture)
- [Data Model Changes](#data-model-changes)
- [How a Trace Gets Reviewed](#how-traces-gets-reviewed-session-flow)
- [Core Features — Where to Look](#core-features--where-to-look)
  - [Concurrent Reservation](#concurrent-reservation)
  - [TTL Recovery for Crashed Sessions](#ttl-recovery-for-crashed-sessions)
  - [Span Highlighting](#span-highlighting)
  - [Feedback Upsert](#feedback-upsert)
  - [Reviewer UI](#reviewer-ui)
- [Key Decisions](docs/decisions.md)
- [Assumptions](#assumptions)
- [Limitations](#limitations-and-things-id-improve-with-more-time)
- [Extra Features](#extra-features-implemented)

---
## TL;DR

Built an annotation queue reviewer flow on top of the existing tracing backend. Multiple reviewers can work a queue concurrently without getting the same trace. Reviewers score traces against a rubric, can highlight spans within trace output JSON fields, and re-score rubric items after submitting. Crashed sessions recover automatically, traces don't stay locked forever in the queue.

---

## Key Highlights

A few things worth calling out in this implementation:

- **Concurrency-safe queue processing** — uses Postgres row-level locking (`FOR UPDATE SKIP LOCKED`) to ensure multiple reviewers can work in parallel without conflicts, without needing external systems like Redis

- **Automatic recovery of stuck sessions (extra feature)** — background TTL job requeues entries left `in_progress` after 30 minutes, preventing permanent lock-ups from crashed browsers without any manual intervention

- **Structured evaluation via rubric system** — supports per-rubric-item scoring and comments, aligning with how LLM evaluation workflows are typically designed (score each rubric item independently, not the trace as a whole)

- **Span-level feedback on trace JSON** — reviewers can select a highlighted span within a specific trace output field and attach that span selection to their feedback record, making feedback precise and traceable back to the exact model output

- **Responsive reviewer experience** — optimistic UI updates show score changes immediately without waiting for the server, with automatic rollback on error; clear empty/error states so reviewers always know where they are in the queue

---

## Problem

LLM teams generate large volumes of traces and need humans to evaluate them systematically, not just spot-check, but work through a queue in order, scoring each trace against defined criteria.

The tricky part is the database layer. A simple `SELECT ... WHERE status = 'pending' LIMIT 1` has a race condition: two reviewers reading at the same moment both see the same queue entry row, both mark it `in_progress`, and one reviewer's feedback records silently overwrite the other's. The starter code had exactly this — a plain SELECT with no locking.

---

## What I added vs the starter code

**Backend:**
- Migration: `reserved_at`, `reserved_by` columns on `queue_entries`; `span_path`, `span_start_index`, `span_end_index` on `feedback`
- `get_next_entry`: upgraded from plain SELECT to `FOR UPDATE SKIP LOCKED` inside a transaction
- Background job *(extra feature)*: `requeue_stuck_entries_loop` — resets stale `in_progress` entries back to `pending`
- New endpoints: `GET /feedback/:id`, `PATCH /feedback/:id`
- Bug fixes from the starter: `complete_entry` now returns 200 + body (was 204), empty queue message aligned with tests

**Frontend (all new):**
- `useQueueSession` — fetches and reserves next entry, handles complete and skip
- `useFeedbackManager` — loads existing feedback, always POSTs (backend upserts), optimistic updates with rollback
- `useSpanSelection` — captures text selection from the JSON viewer, resolves JSON path and character offsets
- `RubricSidebar` + `RubricItemCard` + `RubricItemExpanded` — rubric display with per-key color coding
- `JsonViewer` — syntax-highlighted JSON renderer with `data-path` tags on each field for span targeting
- `HighlightTooltip` — hover tooltip over highlighted spans
- `AnnotationQueuePage` — wires all of the above together

---

## Architecture

The architecture is designed around three independent modules:

- **Queue Management** — queue entries fetched in FIFO order and atomically reserved so multiple reviewers can't annotate the same trace
- **Feedback Management** — scoring, comments, and updates per rubric item via upsert (always POST, DB handles create-vs-update), with optimistic UI updates for responsiveness
- **Rendering & Highlighting** — JSON viewer with precise span selection, enabling feedback records attached to specific highlighted spans with deterministic offset tracking

### Full data flow

[data-flow-diagram](assets/data-flow.png)

### Component structure (frontend)

[frontend-component](assets/frontend-component.png)

---

## Data model changes

Two tables get new columns. Everything else is untouched (starter-code).

**`queue_entries`** — reservation tracking:

| Column | Type | Purpose |
|---|---|---|
| `reserved_at` | `TIMESTAMPTZ` | When the entry was reserved — used by the TTL job to detect stuck sessions |
| `reserved_by` | `VARCHAR(255)` | Who reserved it (reviewer id or "anonymous" — auth is out of scope) |

**`feedback`** — span highlighting:

| Column | Type | Purpose |
|---|---|---|
| `span_path` | `JSONB` | Path to the JSON field being highlighted, e.g. `["outputs", "answer"]` |
| `span_start_index` | `INTEGER` | Start character offset within the string value |
| `span_end_index` | `INTEGER` | End character offset within the string value |

`span_path` is `JSONB` rather than `VARCHAR` because it's a typed array that can contain both strings and integers (object keys and array indices). This matches what `window.getSelection()` produces and what `types.ts` already modeled.

---

## How Traces Gets Reviewed (Session Flow)

1. Reviewer hits the annotation page → `useQueueSession` fetches `GET /queues/:id/entries/next`
2. Backend opens a transaction, locks the first `pending` row with `FOR UPDATE SKIP LOCKED`, updates it to `in_progress`, records `reserved_at` and `reserved_by`, commits — the whole thing takes ~5ms
3. Frontend receives the entry (with full trace data embedded) and renders it
4. In parallel: `useFeedbackManager` calls `GET /traces/:id/feedback` to load existing feedback records — sidebar pre-fills rubric item scores if the queue entry was partially annotated before
5. Reviewer scores rubric items. Each submit goes to `POST /feedback/batch` — the backend upserts on `(trace_id, key)` so create and update are the same call
6. Reviewer clicks **Complete** → `POST /entries/:id/complete` deletes the entry → `useQueueSession` re-fetches and the next entry loads automatically
7. Reviewer clicks **Skip** → `POST /entries/:id/requeue` resets status to `pending` and updates `added_at` (pushes the entry to the back of the FIFO order) → next entry loads

If the browser crashes mid-session, the entry stays locked until the TTL job resets it — see [TTL Recovery for Crashed Sessions](#ttl-recovery-for-crashed-sessions).

---

## Core Features — Where to Look

---

### Concurrent Reservation

The starter code did a plain `SELECT` with no locking. Here's what replaced it and why.

**Backend — reservation logic:**

👉 [`backend/src/services/queues.py` → `get_next_entry()` L138](backend/src/services/queues.py#L138)


**Frontend — why fetching the URL is the reservation:**

👉 [`client/src/hooks/useQueueSession.ts` L7](client/src/hooks/useQueueSession.ts#L7)

The SWR fetch to `/queues/:id/entries/next` is not a read-only call, it also triggers the backend reservation. 

This is documented in a comment at L8–10. `revalidateOnFocus: false` is set deliberately so switching tabs doesn't accidentally reserve a second entry.

**Complete and Skip:**

👉 [`backend/src/services/queues.py` → `complete_entry()` L251](backend/src/services/queues.py#L251)
👉 [`backend/src/services/queues.py` → `requeue_entry()` L284](backend/src/services/queues.py#L284)

Skip resets status to `pending` and bumps `added_at = NOW()` so the entry goes to the back of the FIFO queue rather than immediately coming back up.

---

### TTL Recovery for Crashed Sessions

The reservation status persists in the DB — if a browser crashes, that entry stays `in_progress` forever without a recovery mechanism.

**Background job:** (Extra Feature)

👉 [`backend/src/jobs/requeue_stuck_entries.py` → `requeue_stuck_entries_loop()` L30](backend/src/jobs/requeue_stuck_entries.py#L30)

Runs every `interval_seconds` (default 5 min). Resets any `in_progress` entry where `reserved_at < NOW() - stale_after_seconds` (default 30 min) back to `pending`. 

Both values are env vars — an on-call operator can tune them without a redeploy. The task can also be disabled entirely via `REQUEUE_STUCK_ENTRIES_ENABLED=false`.


**Wired into app startup:**

👉 [`backend/src/main.py` → lifespan L14](backend/src/main.py#L14)

Started as an `asyncio.create_task` in the FastAPI lifespan. Receives a `stop_event` so it shuts down cleanly when the server stops. Can be disabled via `REQUEUE_STUCK_ENTRIES_ENABLED=false`.

---

### Span Highlighting

Reviewers can select a span within a trace input/output JSON string value and attach that highlighted span to their feedback record. Three pieces work together:

**1. Capture the selection (frontend):**

👉 [`client/src/hooks/useSpanSelection.ts` → `useSpanSelection()` L4](client/src/hooks/useSpanSelection.ts#L4)

On `mouseUp` within the JSON viewer, this hook reads `window.getSelection()`, finds the nearest `[data-path]` ancestor to get the JSON path, and measures character offsets using a cloned range. 

Cross-field span selections (where the selection spans a JSON field boundary) are rejected — there's no `data-path` ancestor that contains both ends.

**2. Render highlights in the JSON viewer:**

👉 [`client/src/components/JsonViewer.tsx` → `JsonViewer()` L150](client/src/components/JsonViewer.tsx#L150)

Each string value gets a `data-path` attribute encoding its location in the JSON tree (e.g. `"outputs.answer"`). When feedback with span data exists for a path, the string is split into `[pre, highlight, post]` segments and the middle segment renders as a colored `<mark>`.

**3. Hover tooltip over highlights:**

👉 [`client/src/components/HighlightTooltip.tsx` → `HighlightTooltip()` L12](client/src/components/HighlightTooltip.tsx#L12)

Positioned using the `<mark>` element's bounding rect via `fixed` positioning. `pointer-events-none` so it never blocks mouse events on the text beneath it.

**Storage (backend):**

👉 [`backend/src/services/feedback.py` → `create_feedback_batch()` L20](backend/src/services/feedback.py#L20)
👉 [`backend/src/services/feedback.py` → `update_feedback()` L101](backend/src/services/feedback.py#L101)

`span_path` is serialized to JSON string for storage (asyncpg JSONB requirement) and deserialized back by `_parse_row()` on read.

---

### Feedback Upsert

Scoring a rubric item always calls `POST /feedback/batch`. The backend upserts on `UNIQUE(trace_id, key)` — first submit creates the row, subsequent submits update it. The frontend no longer needs to track whether feedback exists to decide which HTTP method to use.

👉 [`client/src/hooks/useFeedbackManager.ts` → `submitFeedback()` L22](client/src/hooks/useFeedbackManager.ts#L22)
👉 [`backend/src/services/feedback.py` → `create_feedback_batch()` L20](backend/src/services/feedback.py#L20)

```
POST /feedback/batch  →  INSERT ... ON CONFLICT (trace_id, key) DO UPDATE SET ...
```

This makes the backend authoritative — a script, a curl, or a second UI hitting the same endpoint gets an update rather than a duplicate feedback record. `PATCH /feedback/:id` still exists for external callers who want targeted partial updates.

Optimistic updates happen before the server responds — the score badge updates immediately and rolls back on error.

---

### Reviewer UI

The page wires the three domains together. Each section below is independent — the page is just the integration point.

👉 [`client/src/pages/AnnotationQueuePage.tsx`](client/src/pages/AnnotationQueuePage.tsx)
👉 [`client/src/components/RubricSidebar.tsx` → `RubricSidebar()` L31](client/src/components/RubricSidebar.tsx#L31)
👉 [`client/src/components/RubricItemExpanded.tsx` → `RubricItemExpanded()` L32](client/src/components/RubricItemExpanded.tsx#L32)

One rubric item is expanded at a time. When expanded, `RubricItemExpanded` shows the pending span preview (if a span was selected) and the score + comment form. Submitting calls back up to `useFeedbackManager.submitFeedback`.

---

## Key decisions

Full rationale and alternatives considered in [docs/decisions.md](docs/decisions.md). 

Short version:

**Reservation — `FOR UPDATE SKIP LOCKED`**
Three options evaluated: Redis lock, optimistic locking, database row lock. Chose the database lock — no external infrastructure, the lock lasts ~5ms (just the transaction duration), and Postgres handles the concurrency natively without retries or race conditions.

**Feedback upsert — always POST, DB enforces uniqueness**
`UNIQUE(trace_id, key)` constraint on the feedback table + `ON CONFLICT DO UPDATE` in the batch insert. The frontend always POSTs — no create-vs-update branching. Any caller (UI, script, direct API) gets an upsert rather than a duplicate row. `PATCH /feedback/:id` stays for external callers who want targeted partial updates.

**Span storage — three columns**
`span_path JSONB` + `span_start_index INT` + `span_end_index INT`. Three separate columns instead of a single JSONB blob like `{path, start, end}` — keeps queries simple, each field is independently nullable, and a feedback record without a span selection just leaves all three null with no structural overhead.

**Reusing `GET /traces/:id/feedback`**
The alternative was a new `GET /feedback?trace_id=` endpoint. Chose to reuse the existing one — same data, no duplication risk, and it already returned feedback ordered by creation time which is exactly what the sidebar needed to pre-fill scores in the right order.

**TTL recovery — background task, not request-time check**
Piggybacking TTL recovery on the next `GET /entries/next` adds variable latency and needs a nested transaction. A dedicated `asyncio` task on a fixed interval is simpler and independently testable. The 30 minute threshold is intentionally generous — aggressive timeouts would steal entries from reviewers on slow networks.

---

## Assumptions

- **Auth is out of scope** — `reserved_by` is set to `"anonymous"` unless a reviewer id is passed; the schema is ready for auth to be wired in later without changes
- **Span highlighting is single-field only** — span selections that cross JSON field boundaries are rejected with a warning. Multi-field spans would need a different storage model.
- **FIFO within a queue is strict** — `ORDER BY added_at` in the reservation query; skipped entries go to the back via `added_at = NOW()`
- **Last write wins on feedback** — if two reviewers both annotate the same trace for the same rubric item key, the last upsert wins. No locking on feedback rows.

---

## Limitations and things I'd improve with more time

- **Auth** — `reserved_by` is anonymous right now. With a real reviewer identity system this field becomes useful for auditing and preventing one reviewer from stealing another's queue entries
- **Multi-node span selection** — currently limited to single JSON field. Supporting cross-field spans would need anchor + focus node path pairs instead of a single path
- **Queue progress indicator** — `pending_count` is returned per queue but the reviewer UI doesn't show how far through the queue they are. A "X remaining" counter would help pacing
- **TTL is global** — the 30-minute threshold applies to all queues. Some queues might need different thresholds for complex traces with many rubric items vs simpler ones

---

## Extra features implemented

**TTL recovery for crashed sessions** — the core requirement only asks for reservation, not recovery. Without a recovery mechanism, a crashed browser permanently locks a queue entry. Full implementation detail in [Core Features → TTL Recovery](#ttl-recovery-for-crashed-sessions).

**Optimistic feedback submission** — score badge updates immediately on submit, reverts to the previous state if the server returns an error. Keeps the reviewer flow snappy on slower connections.

**Per-rubric color coding** — each rubric key gets a consistent color (purple, blue, amber, etc.) derived by hashing the key name. Highlights in the JSON viewer match the sidebar color for that key.

**Span overlap detection** — if the reviewer selects a span that overlaps an existing highlighted span for a different rubric item key, a warning shows before submit.

**Distinct error states** — network failure and "queue complete" are handled separately so a server error doesn't show as "Queue complete" to the reviewer.

**Collapsed panel previews** — trace input/output panels show a one-line content preview when collapsed so reviewers can decide which to expand without opening both.