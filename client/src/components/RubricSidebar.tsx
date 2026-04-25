import { useState, useRef, forwardRef, useImperativeHandle } from "react";
import { Keyboard } from "lucide-react";
import { useQueueRubric } from "../hooks/useApi";
import { RubricItemCard } from "./RubricItemCard";
import type { RubricItemExpandedHandle } from "./RubricItemExpanded";
import type { Feedback, FeedbackSpan } from "../types";

type Props = {
  queueId: string;
  feedbackMap: Map<string, Feedback>;
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
  onOpenLegend?: () => void;
};

export interface RubricSidebarHandle {
  setScore: (score: number) => void;
  submitActive: () => void;
  cycleNext: () => void;
}

export const RubricSidebar = forwardRef<RubricSidebarHandle, Props>(
  function RubricSidebar(
    { queueId, feedbackMap, isFeedbackLoading, onSubmit, pendingSpan, pendingText, overlapWarning, onClearSpan, onOpenLegend },
    ref
  ) {
    const { rubric, isLoading } = useQueueRubric(queueId);
    // Only one card expanded at a time
    const [activeKey, setActiveKey] = useState<string | null>(null);
    // Ref to the currently expanded rubric item form — used for keyboard score/submit.
    const activeItemRef = useRef<RubricItemExpandedHandle | null>(null);

    useImperativeHandle(ref, () => ({
      setScore: (score) => activeItemRef.current?.setScore(score),
      submitActive: () => activeItemRef.current?.submit(),
      cycleNext: () => {
        const keys = rubric.map((r) => r.feedback_key);
        if (keys.length === 0) return;
        const curIdx = activeKey != null ? keys.indexOf(activeKey) : -1;
        setActiveKey(keys[(curIdx + 1) % keys.length]);
      },
    }), [rubric, activeKey]);

    if (isLoading) {
      return (
        <div className="w-[30%] min-w-72 border-l border-gray-200 bg-white p-5 text-sm text-gray-400">
          Loading rubric...
        </div>
      );
    }

    return (
      <div className="w-[30%] min-w-72 border-l border-gray-200 bg-gray-50 flex flex-col overflow-hidden">
        {/* Rubric cards — header is now in the page-level navbar */}
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
          {rubric.length === 0 ? (
            <p className="text-sm text-gray-400 text-center pt-4">
              No rubric items defined for this queue.
            </p>
          ) : (
            rubric.map((item) => (
              <RubricItemCard
                key={item.id}
                item={item}
                feedback={feedbackMap.get(item.feedback_key)}
                isOpen={activeKey === item.feedback_key}
                onToggle={() =>
                  setActiveKey(activeKey === item.feedback_key ? null : item.feedback_key)
                }
                onSubmit={onSubmit}
                isFeedbackLoading={isFeedbackLoading}
                pendingSpan={pendingSpan}
                pendingText={pendingText}
                overlapWarning={overlapWarning}
                onClearSpan={onClearSpan}
                expandedRef={activeKey === item.feedback_key ? activeItemRef : undefined}
              />
            ))
          )}
        </div>

        {/* Footer shortcut hint */}
        <button
          onClick={onOpenLegend}
          className="shrink-0 flex items-center justify-center gap-2 border-t border-gray-200 py-2.5 text-xs text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
        >
          <Keyboard className="w-3.5 h-3.5" />
          Press <kbd className="font-mono font-semibold text-gray-500">?</kbd> to view shortcuts
        </button>
      </div>
    );
  }
);
