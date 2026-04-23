import { useState } from "react";
import { useQueueRubric } from "../hooks/useApi";
import { RubricItemCard } from "./RubricItemCard";
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
};

export function RubricSidebar({ queueId, feedbackMap, onSubmit }: Props) {
  const { rubric, isLoading } = useQueueRubric(queueId);

  // Only one card expanded at a time
  const [activeKey, setActiveKey] = useState<string | null>(null);

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
            />
          ))
        )}
      </div>
    </div>
  );
}
