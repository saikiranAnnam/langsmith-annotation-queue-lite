# Engineering Challenges & How I Fixed Them

A running log of real bugs and product gaps encountered while building the annotation queue system — documented in STAR format (Situation, Task, Action, Result).

---

## Challenge 1 — Finishing Layer: Keyboard Shortcuts, Loading States, and Edge Cases

### Situation
The core annotation workflow was functional — reviewers could open a trace, score rubric items, and complete or skip entries. But the experience felt rough. There were no keyboard shortcuts, so reviewers had to reach for the mouse on every action. Loading states showed a blank screen or plain text. Network failures silently swallowed errors with no way to retry. Selecting text across two JSON fields produced no feedback, leaving reviewers confused about why no highlight appeared.

### Task
Add a proper finishing layer on top of the working core: keyboard navigation for the annotation flow, skeleton loaders while data is fetching, a meaningful empty-queue screen, error toasts with a retry option, and an inline message for cross-field text selections.

### Action
- Created `useKeyboardShortcuts.ts` — a hook that listens on `keydown` and routes keys to the appropriate handler. Keys `1`–`9` set scores `0.1`–`0.9`, `0` sets `1.0`, `Enter` submits the active rubric form, `Tab` cycles to the next rubric item, `N` completes the entry, `S` skips it, and `?` toggles a shortcut legend modal. Guards prevent the shortcuts from firing when focus is inside an `<input>` or `<textarea>`.
- Threaded an imperative handle (`forwardRef` + `useImperativeHandle`) from `RubricItemExpanded` → `RubricItemCard` → `RubricSidebar`, so the page-level keyboard hook can call `setScore()` and `submit()` on whichever rubric card is currently open without prop-drilling state.
- Replaced the plain `Loading...` text with a skeleton layout matching the two-column page structure — placeholder boxes for the header, content panels, and sidebar cards, all with `animate-pulse`.
- Replaced the plain `Queue complete` text with a full-screen state: a large green checkmark, a heading, and a `Check for new entries` refresh button that calls `mutate()` on the SWR key.
- Replaced inline error banners for skip/complete failures with `toast.error(...)` calls from Sonner, each with a `Retry` action button. Used a stable handler ref so the retry closure always calls the latest function version.
- Added `crossFieldWarning` state to `useSpanSelection` — when a text selection crosses a JSON field boundary, an amber inline banner appears: *"Please select within a single field to attach a highlight."* It auto-dismisses after 3 seconds.

### Result
Reviewers can score, submit, cycle rubrics, skip, and complete entries entirely from the keyboard. The page feels responsive during loads instead of showing blank space. Errors surface with one-click retry rather than requiring a manual page reload. Cross-field selection attempts now give clear guidance instead of silently doing nothing.

---

## Challenge 2 — Pending Count Badge Drops When You Open a Trace

### Situation
After adding a `pending_count` badge to each queue card on the Queues page, reviewers noticed the number would drop by one the moment they clicked into a queue to start annotating — before they had reviewed or scored anything. This felt broken: the count was supposed to represent work still to be done, but it was shrinking just from opening the page.

### Task
Fix the `pending_count` so it only decreases when an entry is actually completed, not when a reviewer merely opens it.

### Action
Traced the bug to the SQL queries in `services/queues.py`. All three `pending_count` aggregations used `FILTER (WHERE qe.status = 'pending')`. When a reviewer opens a trace, the backend atomically sets that entry to `in_progress` via `FOR UPDATE SKIP LOCKED`. So the entry immediately left the `pending` bucket even though it hadn't been reviewed yet.

Changed all three queries to `FILTER (WHERE qe.status IN ('pending', 'in_progress'))`. Now both statuses are counted as "work remaining" — only `completed` entries are excluded.

### Result
The badge stays stable while a reviewer is actively working on a trace. It only drops when they click `Complete & Next`, which is the moment the work is genuinely done.

---

## Challenge 3 — Progress Counter Always Shows Same Number in Numerator and Denominator

### Situation
After adding the `pending_count / total_count` progress display to the annotation page header (e.g. "3 of 5 Pending"), reviewers noticed the denominator was changing. After completing a few entries the counter would show something like "2 / 2" instead of "2 / 5". The total appeared to shrink alongside the remaining count, making it impossible to see actual progress through the queue.

### Task
Fix the `total_count` so it represents all entries ever added to the queue — a stable denominator that only grows when new traces are added, never shrinks.

### Action
Investigated the `complete_entry` function in `services/queues.py`. It was running `DELETE FROM queue_entries` — entries were physically removed from the table on completion. Since `total_count` was `COUNT(qe.id)` (all rows in the table), it shrank by one each time an entry was completed, moving in lockstep with `pending_count`.

Changed `complete_entry` to `UPDATE queue_entries SET status = 'completed'` instead of deleting the row. Completed entries now stay in the table permanently. The `total_count = COUNT(qe.id)` query naturally includes all statuses, giving a stable total. The `get_next_entry` query already filtered for `WHERE status = 'pending'` so completed entries are never re-served. Updated the response message and the one test assertion that checked for the old deletion-based message.

Also moved the progress display from plain text under the queue name to an inline amber badge — "3 of 5 Pending" — placed alongside the Skip and Complete buttons in the header, and removed the standalone badge from the Queues list page since the detail is more meaningful in context.

### Result
The progress counter now shows genuine progress. "2 of 10 Pending" means 8 entries have been completed. The denominator is fixed for the lifetime of the queue, giving reviewers an accurate sense of how far through the work they are.

---

## Challenge 4 — Refreshing the Page Makes the Queue Appear Empty

### Situation
This was the most disruptive bug: if a reviewer refreshed the annotation page mid-session, the queue would show as complete — "All entries have been reviewed" — even when there were plenty of traces left. Repeated refreshes made it progressively worse, and restarting a session could leave an entire queue stuck with no way to recover without manual database intervention.

### Task
Make page refresh safe. A reviewer should land back on the same trace they were working on, not lose their place and burn an entry.

### Action
Traced the root cause to how `GET /queues/{queueId}/entries/next` worked. Every call — whether first load or a refresh — would atomically select the next `pending` entry and set it to `in_progress`. On refresh:

1. First page load reserves Entry A → `in_progress`
2. Refresh calls the endpoint again
3. Entry A is `in_progress`, not `pending`, so the query skips it
4. Entry B gets reserved → `in_progress`
5. After enough refreshes, every entry is stuck in `in_progress` and the queue looks empty

The fix was to make the reservation **idempotent**. Three changes working together:

- **`client/src/lib/reviewerId.ts`** — on first visit, generates a `crypto.randomUUID()` and persists it in `localStorage`. Every subsequent visit from the same browser reuses the same ID.
- **`useQueueSession.ts`** — appends `?reviewer_id=<uuid>` to the SWR fetch URL so the ID travels with every request.
- **`services/queues.py` (`get_next_entry`)** — before the `FOR UPDATE SKIP LOCKED` reservation block, added a lookup: *does this `reviewer_id` already have an `in_progress` entry in this queue?* If yes, skip the reservation entirely and return that same entry. If no, proceed with reserving the next `pending` one as before.

Also updated the FastAPI router to accept `reviewer_id` as a query parameter (defaulting to `"anonymous"` for backwards compatibility).

### Result
Refreshing the page now returns the reviewer to the exact trace they were working on. No new entry is reserved, no entry is left orphaned in `in_progress`. The fix also handles tab restores and hard reloads. For cases where a reviewer genuinely abandons a session without completing or skipping, the `reserved_by` field on the entry allows TTL recovery to target those rows specifically when that mechanism is wired in.

---

*Last updated: 2026-04-25*
