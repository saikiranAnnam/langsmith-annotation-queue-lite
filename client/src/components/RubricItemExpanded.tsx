import { useState, useEffect } from "react";
import { Loader2, CircleCheckBig, SendHorizonal } from "lucide-react";
import { RubricScoreInput } from "./RubricScoreInput";
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

export function RubricItemExpanded({ item, existing, onSubmit }: Props) {
  const [score, setScore] = useState(existing?.score?.toString() ?? "");
  const [comment, setComment] = useState(existing?.comment ?? "");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  // Saved baseline — updated after each successful save so dirty check stays accurate
  const [savedScore, setSavedScore] = useState(existing?.score?.toString() ?? "");
  const [savedComment, setSavedComment] = useState(existing?.comment ?? "");

  // True only when values differ from last saved state
  const isDirty = score !== savedScore || comment !== savedComment;

  // Pre-fill when existing feedback loads (e.g. after entry transition)
  useEffect(() => {
    const s = existing?.score?.toString() ?? "";
    const c = existing?.comment ?? "";
    setScore(s);
    setComment(c);
    setSavedScore(s);
    setSavedComment(c);
    setError(null);
    setSaved(false);
  }, [existing?.id]);

  // Reset saved state back to default after 2s so button returns to "Save feedback"
  useEffect(() => {
    if (!saved) return;
    const t = setTimeout(() => setSaved(false), 2000);
    return () => clearTimeout(t);
  }, [saved]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaved(false);
    setIsSubmitting(true);
    try {
      // Run the API call and a 300ms minimum delay in parallel so the spinner never flashes
      await Promise.all([
        onSubmit(item.feedback_key, score !== "" ? parseFloat(score) : null, comment),
        new Promise((res) => setTimeout(res, 300)),
      ]);
      setSaved(true);
      setSavedScore(score);
      setSavedComment(comment);
    } catch {
      setError("Failed to save. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-3 pt-3 mt-1 border-t border-gray-100"
    >
      <p className="text-xs text-gray-500 leading-relaxed">{item.description}</p>

      <RubricScoreInput
        value={score}
        onChange={(val) => { setScore(val); setSaved(false); }}
      />

      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-gray-600">Comment</label>
        <textarea
          value={comment}
          onChange={(e) => { setComment(e.target.value); setSaved(false); }}
          placeholder="Why did you give this score?"
          rows={3}
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {error && <p className="text-xs text-red-500">{error}</p>}

      {/* Button transitions between default → saving → saved, all inline */}
      <button
        type="submit"
        disabled={!isDirty || isSubmitting || saved}
        className={`w-full h-9 flex items-center justify-center gap-2 text-sm font-medium text-white rounded-lg transition-all duration-300 ${
          saved
            ? "bg-green-500 scale-[1.01]"
            : isSubmitting
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
        ) : saved ? (
          <>
            <CircleCheckBig className="w-4 h-4 animate-bounce" />
            Saved!
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
