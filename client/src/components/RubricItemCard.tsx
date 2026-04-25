import { CircleCheckBig, ChevronDown, ChevronRight } from "lucide-react";
import { RubricItemExpanded } from "./RubricItemExpanded";
import type { RubricItemExpandedHandle } from "./RubricItemExpanded";
import type { Feedback, FeedbackSpan, QueueRubricItem } from "../types";
import { getRubricColor } from "../lib/rubricColors";

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
  isFeedbackLoading?: boolean;
  pendingSpan?: FeedbackSpan | null;
  pendingText?: string | null;
  overlapWarning?: boolean;
  onClearSpan?: () => void;
  expandedRef?: React.Ref<RubricItemExpandedHandle>;
};

export function RubricItemCard({ item, feedback, isOpen, onToggle, onSubmit, isFeedbackLoading, pendingSpan, pendingText, overlapWarning, onClearSpan, expandedRef }: Props) {
  const colors = getRubricColor(item.feedback_key);
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
          <RubricItemExpanded
            ref={expandedRef}
            item={item}
            existing={feedback}
            onSubmit={onSubmit}
            isFeedbackLoading={isFeedbackLoading}
            pendingSpan={pendingSpan}
            pendingText={pendingText}
            overlapWarning={overlapWarning}
            onClearSpan={onClearSpan}
          />
        </div>
      )}
    </div>
  );
}
