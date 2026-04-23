import { useState, useEffect } from "react";
import { useTraceFeedback } from "./useApi";
import { API_BASE, postData, patchData } from "../lib/api";
import type { Feedback, FeedbackSpan } from "../types";

export function useFeedbackManager(traceId: string | null) {
  const { feedback: existing } = useTraceFeedback(traceId);

  // Local map of key → Feedback 
  // so we can update individual items without re-fetching all
  const [feedbackMap, setFeedbackMap] = useState<Map<string, Feedback>>(new Map());

  // When the trace changes, rebuild the map from server data
  useEffect(() => {
    const map = new Map<string, Feedback>();
    existing.forEach((f) => map.set(f.key, f));
    setFeedbackMap(map);
  }, [traceId, existing.length]);

  const submitFeedback = async (
    key: string,
    score: number | null,
    comment: string,
    span?: FeedbackSpan
  ) => {
    const prior = feedbackMap.get(key);

    // Show the change immediately — don't wait for the server
    const optimistic = {
      ...(prior ?? {}),
      key,
      score,
      comment,
      span_path: span?.span_path,
      span_start_index: span?.span_start_index,
      span_end_index: span?.span_end_index,
    } as Feedback;
    setFeedbackMap((prev) => new Map(prev).set(key, optimistic));

    try {
      let saved: Feedback;

      if (prior?.id) {
        // Feedback already exists for this key — update it
        saved = await patchData<Feedback>(`${API_BASE}/feedback/${prior.id}`, {
          score,
          comment,
          ...(span ?? {}),
        });
      } else {
        // First time scoring this rubric item — create it
        const batch = await postData<Feedback[]>(`${API_BASE}/feedback/batch`, [
          { trace_id: traceId, key, score, comment, ...(span ?? {}) },
        ]);
        saved = batch[0];
      }

      setFeedbackMap((prev) => new Map(prev).set(key, saved));
    } catch (err) {
      // Server rejected it — roll back to what was there before
      setFeedbackMap((prev) => {
        const next = new Map(prev);
        prior ? next.set(key, prior) : next.delete(key);
        return next;
      });
      throw err;
    }
  };

  return { feedbackMap, submitFeedback };
}
