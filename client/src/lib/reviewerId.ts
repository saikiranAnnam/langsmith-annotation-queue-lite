const STORAGE_KEY = "tracedog_reviewer_id";

// Stable ID persisted in localStorage so the same browser session always
// identifies as the same reviewer. Used by the backend to return the
// existing in_progress reservation on page refresh instead of reserving
// a brand-new entry each time.
export function getReviewerId(): string {
  let id = localStorage.getItem(STORAGE_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(STORAGE_KEY, id);
  }
  return id;
}
