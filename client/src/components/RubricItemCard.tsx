import { CircleCheckBig, ChevronDown, ChevronRight } from "lucide-react";
import { RubricItemExpanded } from "./RubricItemExpanded";
import type { Feedback, FeedbackSpan, QueueRubricItem } from "../types";

// Soft accent colors per rubric key — fallback to gray for unknown keys
const KEY_COLORS: Record<string, { dot: string; badge: string }> = {
  accuracy:    { dot: "bg-purple-400", badge: "bg-purple-50 text-purple-700 border-purple-100" },
  helpfulness: { dot: "bg-blue-400",   badge: "bg-blue-50 text-blue-700 border-blue-100" },
  tone:        { dot: "bg-amber-400",  badge: "bg-amber-50 text-amber-700 border-amber-100" },
};
const DEFAULT_COLOR = { dot: "bg-gray-300", badge: "bg-gray-50 text-gray-600 border-gray-100" };

type Props = {
  item: QueueRubricItem;
  feedback: Feedback | undefined;
  isOpen: boolean;
  onToggle: () => void;
  onSubmit: (
    key: string,
    score: number | null,
    comment: string,
    span?: FeedbackSpan
  ) => Promise<void>;
};

export function RubricItemCard({ item, feedback, isOpen, onToggle, onSubmit }: Props) {
  const colors = KEY_COLORS[item.feedback_key.toLowerCase()] ?? DEFAULT_COLOR;
  const isCompleted = feedback?.score != null;

  return (
    <div
      className={`rounded-xl border bg-white transition-colors ${
        isOpen ? "border-blue-200" : "border-gray-200 hover:border-gray-300"
      }`}
    >
      <button
        onClick={onToggle}
        className="w-full flex items-start gap-3 px-4 py-3 text-left"
      >
        {/* Dot — always top-aligned so it never shifts between states */}
        <span className={`w-2 h-2 rounded-full shrink-0 mt-1.5 ${colors.dot}`} />

        {/* Content area — always key name on line 1, extras below when collapsed */}
        <div className="flex-1 flex flex-col gap-0.5 min-w-0">
          <span className="text-sm font-semibold text-gray-900">
            {item.feedback_key}
          </span>
          {!isOpen && (
            <>
              {/* When scored, hide description and show score + comment only */}
              {isCompleted ? (
                <>
                  <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
                    <span className="text-xs font-semibold text-green-700 bg-green-500/10 ring-1 ring-inset ring-green-500/20 px-2 py-0.5 rounded-md shrink-0">
                      Score: {feedback!.score!.toFixed(1)}
                    </span>
                    {feedback!.comment && (
                      <span className="text-xs font-medium text-slate-500 bg-slate-500/8 ring-1 ring-inset ring-slate-400/20 px-2 py-0.5 rounded-md truncate">
                        {feedback!.comment}
                      </span>
                    )}
                  </div>
                </>
              ) : (
                <span className="text-xs text-gray-400 truncate">{item.description}</span>
              )}
            </>
          )}
        </div>

        {/* Check icon beside the chevron when graded, chevron always top-aligned */}
        {isCompleted && !isOpen && (
          <CircleCheckBig className="w-4 h-4 text-green-500 shrink-0 mt-0.5" />
        )}
        {isOpen ? (
          <ChevronDown className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
        ) : (
          <ChevronRight className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
        )}
      </button>

      {isOpen && (
        <div className="px-4 pb-4">
          <RubricItemExpanded item={item} existing={feedback} onSubmit={onSubmit} />
        </div>
      )}
    </div>
  );
}
