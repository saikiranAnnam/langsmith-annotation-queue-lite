import type { Feedback } from "../types";

interface Props {
  feedback: Feedback;
  // The bounding rect of the <mark> element the user is hovering over.
  // We use this to position the tooltip directly above it.
  anchorRect: DOMRect;
}

// A small dark tooltip that floats above a highlighted span in the JSON viewer.
// pointer-events-none so it never gets in the way of mouse events beneath it.
export function HighlightTooltip({ feedback, anchorRect }: Props) {
  return (
    <div
      style={{
        position: "fixed",
        top: anchorRect.top - 8,
        left: anchorRect.left,
        transform: "translateY(-100%)",
        zIndex: 50,
      }}
      className="pointer-events-none bg-gray-900 text-white text-xs rounded-md shadow-lg px-3 py-2 max-w-xs"
    >
      {/* key: score on one line, comment below */}
      <p className="font-semibold text-amber-400">
        {feedback.key}
        {feedback.score != null && (
          <span className="text-gray-300 font-normal ml-1">: {feedback.score.toFixed(1)}</span>
        )}
      </p>
      {feedback.comment && (
        <p className="text-gray-300 mt-0.5 italic">{feedback.comment}</p>
      )}
    </div>
  );
}
