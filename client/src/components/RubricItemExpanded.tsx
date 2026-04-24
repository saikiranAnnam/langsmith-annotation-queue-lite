import { useState, useEffect, useRef } from "react";
import { Loader2, SendHorizonal } from "lucide-react";
import { RubricScoreInput } from "./RubricScoreInput";
import { toast } from "sonner";
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
  // True while existing feedback for this trace is still being fetched.
  isFeedbackLoading?: boolean;
  // The span the reviewer highlighted in the JSON viewer, if any.
  // Shown as a small banner so they can confirm before submitting.
  pendingSpan?: FeedbackSpan | null;
  pendingText?: string | null;
  // True when the pending span overlaps an already-saved highlight.
  overlapWarning?: boolean;
  onClearSpan?: () => void;
};

export function RubricItemExpanded({ item, existing, onSubmit, isFeedbackLoading, pendingSpan, pendingText, overlapWarning, onClearSpan }: Props) {
  const [score, setScore] = useState(existing?.score?.toString() ?? "");
  const [comment, setComment] = useState(existing?.comment ?? "");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Explicit flag — only set by reviewer input, cleared on save or queue entry transition.
  const [hasChanges, setHasChanges] = useState(false);

  const isDirty = hasChanges || !!pendingSpan;

  // Pre-fill when existing feedback loads (e.g. after entry transition)
  useEffect(() => {
    setScore(existing?.score?.toString() ?? "");
    setComment(existing?.comment ?? "");
    setHasChanges(false);
    setError(null);
  }, [existing?.id]);

  // Clear the pending span only when the reviewer switches to a *different* item —
  // not on initial mount, otherwise opening a card would immediately wipe the span.
  const hasMounted = useRef(false);
  useEffect(() => {
    if (!hasMounted.current) { hasMounted.current = true; return; }
    onClearSpan?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [item.id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    const hadSpan = !!pendingSpan;
    try {
      await Promise.all([
        onSubmit(
          item.feedback_key,
          score !== "" ? parseFloat(score) : null,
          comment,
          pendingSpan ?? undefined
        ),
        new Promise((res) => setTimeout(res, 300)),
      ]);
      onClearSpan?.();
      setHasChanges(false);
      toast.success(hadSpan ? "Feedback saved with highlight" : "Feedback saved");
    } catch {
      setError("Failed to save. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isFeedbackLoading) {
    return (
      <div className="flex flex-col gap-3 pt-3 mt-1 border-t border-gray-100 animate-pulse">
        <div className="h-3 bg-gray-100 rounded w-3/4" />
        <div className="h-8 bg-gray-100 rounded-lg" />
        <div className="h-16 bg-gray-100 rounded-lg" />
        <div className="h-9 bg-gray-100 rounded-lg" />
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-3 pt-3 mt-1 border-t border-gray-100"
    >
      <p className="text-xs text-gray-500 leading-relaxed">{item.description}</p>

      <RubricScoreInput
        value={score}
        onChange={(val) => { setScore(val); setHasChanges(true); }}
      />

      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-gray-600">Comment</label>
        <textarea
          value={comment}
          onChange={(e) => { setComment(e.target.value); setHasChanges(true); }}
          placeholder="Why did you give this score?"
          rows={3}
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Shows the span the reviewer highlighted in the JSON viewer.
          They can dismiss it with ✕ if they don't want to attach it. */}
      {pendingSpan && (
        <div className={`flex items-center justify-between text-xs rounded-lg px-3 py-2 gap-2 border ${
          overlapWarning
            ? "bg-orange-50 border-orange-300"
            : "bg-amber-50 border-amber-200"
        }`}>
          <div className="min-w-0">
            <p className={`font-medium ${overlapWarning ? "text-orange-800" : "text-amber-800"}`}>
              {overlapWarning ? "Overlaps existing highlight" : "Highlighted Text"}
            </p>
            <p className={`truncate ${overlapWarning ? "text-orange-700" : "text-amber-700"}`}>
              {overlapWarning
                ? "This selection overlaps a saved highlight — submitting will skip the overlapping portion."
                : (pendingText ?? pendingSpan.span_path.join("."))}
            </p>
          </div>
          <button
            type="button"
            onClick={onClearSpan}
            className={`shrink-0 leading-none ${overlapWarning ? "text-orange-500 hover:text-orange-700" : "text-amber-500 hover:text-amber-700"}`}
          >
            ✕
          </button>
        </div>
      )}

      {error && <p className="text-xs text-red-500">{error}</p>}

      <button
        type="submit"
        disabled={!isDirty || isSubmitting}
        className={`w-full h-9 flex items-center justify-center gap-2 text-sm font-medium text-white rounded-lg transition-colors ${
          isSubmitting
            ? "bg-blue-600 opacity-70"
            : isDirty
            ? "bg-blue-600 hover:bg-blue-700"
            : "bg-blue-300 cursor-not-allowed"
        }`}
      >
        {isSubmitting ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Saving...
          </>
        ) : (
          <>
            <SendHorizonal className="w-4 h-4 -rotate-45 shrink-0 -translate-y-0.5" />
            Submit Feedback
          </>
        )}
      </button>
    </form>
  );
}
