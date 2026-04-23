import { useState, useEffect } from "react";
import type { Feedback, FeedbackSpan, QueueRubricItem } from "../types";

type Props = {
  item: QueueRubricItem;
  existing: Feedback | undefined;
  onSubmit: (
    key: string,
    score: number | null,
    comment: string,
    span?: FeedbackSpan
  ) => Promise<void>;
};

export function RubricItemForm({ item, existing, onSubmit }: Props) {
  const [score, setScore] = useState<string>(existing?.score?.toString() ?? "");
  const [comment, setComment] = useState<string>(existing?.comment ?? "");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  // Pre-fill when existing feedback loads (e.g. after entry transition)
  useEffect(() => {
    setScore(existing?.score?.toString() ?? "");
    setComment(existing?.comment ?? "");
    setError(null);
    setSaved(false);
  }, [existing?.id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaved(false);
    setIsSubmitting(true);

    try {
      await onSubmit(
        item.feedback_key,
        score !== "" ? parseFloat(score) : null,
        comment
      );
      setSaved(true);
    } catch {
      setError("Failed to save. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 pt-1">
      <p className="text-xs text-gray-500">{item.description}</p>

      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-gray-600">
          Score (0.0 – 1.0)
        </label>
        <input
          type="number"
          min="0"
          max="1"
          step="0.1"
          value={score}
          onChange={(e) => { setScore(e.target.value); setSaved(false); }}
          placeholder="0.0"
          className="w-full border border-gray-200 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-gray-600">Comment</label>
        <textarea
          value={comment}
          onChange={(e) => { setComment(e.target.value); setSaved(false); }}
          placeholder="Why did you give this score?"
          rows={3}
          className="w-full border border-gray-200 rounded-md px-3 py-1.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {error && <p className="text-xs text-red-500">{error}</p>}

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full py-1.5 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
      >
        {isSubmitting ? "Saving..." : saved ? "Saved ✓" : "Save"}
      </button>
    </form>
  );
}
