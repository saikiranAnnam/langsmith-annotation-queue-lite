import { CheckCircle2 } from "lucide-react";

type Props = {
  feedbackKey: string;
  score: number;
  comment: string | null;
  badgeClass: string;
};

export function RubricCompletedPreview({ feedbackKey, score, comment, badgeClass }: Props) {
  return (
    <div className="flex items-center gap-2 flex-1 min-w-0">
      <span className={`shrink-0 text-xs font-semibold px-2.5 py-0.5 rounded-full border ${badgeClass}`}>
        {feedbackKey} · {score.toFixed(1)}
      </span>
      {comment && (
        <span className="flex-1 text-xs text-gray-400 truncate">{comment}</span>
      )}
      <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0 ml-auto" />
    </div>
  );
}
