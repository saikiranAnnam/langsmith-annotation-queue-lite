import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Maximize2, Minimize2, CircleCheckBig, AlertCircle, Loader2 } from "lucide-react";
import { useQueueSession } from "../hooks/useQueueSession";
import { useQueue } from "../hooks/useApi";
import { useFeedbackManager } from "../hooks/useFeedbackManager";
import { RubricSidebar } from "../components/RubricSidebar";
import { JsonViewer } from "../components/JsonViewer";
import { useSpanSelection } from "../hooks/useSpanSelection";

export function AnnotationQueuePage() {
  const { queueId } = useParams<{ queueId: string }>();
  const { queue } = useQueue(queueId ?? null);
  // useQueueSession handles fetching the next entry and reserving it on the backend
  const { entry, isLoading, isEmpty, isError, completeEntry, skipEntry } =
    useQueueSession(queueId!);

  const [actionError, setActionError] = useState<string | null>(null);
  const [isActioning, setIsActioning] = useState(false);

  const { feedbackMap, isFeedbackLoading, submitFeedback } = useFeedbackManager(
    entry?.trace_id ?? null
  );

  // Feedbacks that have span data attached — passed to JsonViewer so it can
  // render amber highlights directly on the relevant string values.
  const highlights = Array.from(feedbackMap.values()).filter(
    (f) => f.span_path != null
  );

  const { pendingSpan, pendingText, overlapWarning, clearSpan, handleMouseUp } = useSpanSelection(highlights);

  // Clear any pending span when the reviewer moves to a new entry so a span
  // selected on entry A cannot be accidentally saved against entry B's feedback.
  useEffect(() => {
    clearSpan();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entry?.trace_id]);

  // Both panels expanded by default so reviewers see the full content on load
  const [inputOpen, setInputOpen] = useState(true);
  const [outputOpen, setOutputOpen] = useState(true);

  // Still waiting for the first entry to come back from the backend
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500">
        Loading...
      </div>
    );
  }

  // Network or server error loading the entry — don't show "Queue complete" misleadingly
  if (isError) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 text-gray-500">
        <AlertCircle className="w-8 h-8 text-red-400" />
        <p className="text-base font-medium text-gray-700">Failed to load queue entry</p>
        <p className="text-sm">Check your connection and refresh the page.</p>
      </div>
    );
  }

  // Backend returned 404 — no pending entries left in this queue
  if (isEmpty) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3 text-gray-500">
        <p className="text-lg font-medium">Queue complete</p>
        <p className="text-sm">No pending entries remaining.</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Two-column header mirroring the content layout below */}
      <div className="bg-white flex items-center shrink-0 h-16">
        {/* Left column — aligns with the annotation/input-output panel */}
        <div className="flex-1 flex items-center justify-between px-6 h-full border-b border-gray-200">
          <div>
            <p className="text-[10px] font-medium text-gray-400 uppercase tracking-widest">Queue</p>
            <p className="text-base font-semibold text-gray-900 leading-snug">{queue?.name ?? "..."}</p>
          </div>
          <div className="flex items-center gap-2.5">
            {actionError && (
              <div className="flex items-center gap-1.5 text-xs text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-1.5 max-w-56">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">{actionError}</span>
              </div>
            )}
            {/* Skip requeues the entry so another reviewer can pick it up later */}
            <button
              disabled={isActioning}
              onClick={async () => {
                try {
                  setActionError(null);
                  setIsActioning(true);
                  await skipEntry();
                } catch {
                  setActionError("Failed to skip. Please try again.");
                } finally {
                  setIsActioning(false);
                }
              }}
              className="h-8 px-4 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150"
            >
              {isActioning ? <Loader2 className="w-4 h-4 animate-spin" /> : "Skip"}
            </button>
            {/* Complete marks the entry done and immediately loads the next one */}
            <button
              disabled={isActioning}
              onClick={async () => {
                try {
                  setActionError(null);
                  setIsActioning(true);
                  await completeEntry();
                } catch {
                  setActionError("Failed to complete. Please try again.");
                } finally {
                  setIsActioning(false);
                }
              }}
              className="h-8 flex items-center gap-2 px-4 text-sm font-semibold text-white bg-green-600 rounded-md shadow-sm hover:bg-green-700 active:bg-green-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150"
            >
              {isActioning ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <CircleCheckBig className="w-3.5 h-3.5 shrink-0" />
              )}
              {isActioning ? "Working..." : "Complete & Next"}
            </button>
          </div>
        </div>
        {/* Right column — aligns with the feedback rubric sidebar */}
        <div className="w-[30%] min-w-72 border-l border-gray-200 px-5 h-full flex items-center">
          <div className="flex flex-col gap-1">
            <h3 className="text-md font-semibold text-gray-900">Feedback Rubrics</h3>
            <p className="text-xs text-gray-400">Select a rubric to expand and annotate.</p>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex flex-col gap-4 p-6 overflow-auto">
          {/* Input panel */}
          <div className="border border-gray-200 rounded-lg bg-white overflow-hidden">
            <button
              onClick={() => setInputOpen((v) => !v)}
              className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-3 min-w-0">
                <span className="text-xs font-semibold uppercase tracking-wide text-gray-400 shrink-0">
                  Input
                </span>
                {/* Preview only shown when collapsed — hidden when expanded since full content is visible below */}
                {!inputOpen && (
                  <span className="text-xs text-gray-500 truncate">
                    {entry?.trace.inputs?.question}
                  </span>
                )}
              </div>
              {/* Maximize2 = expand (collapsed state), Minimize2 = collapse (expanded state) */}
              {inputOpen ? (
                <Minimize2 className="w-4 h-4 text-gray-400 shrink-0" />
              ) : (
                <Maximize2 className="w-4 h-4 text-gray-400 shrink-0" />
              )}
            </button>
            {inputOpen && (
              <div onMouseUp={handleMouseUp}>
                <JsonViewer value={entry?.trace.inputs} path="inputs" highlights={highlights} />
              </div>
            )}
          </div>

          {/* Output panel */}
          <div className="border border-gray-200 rounded-lg bg-white overflow-hidden">
            <button
              onClick={() => setOutputOpen((v) => !v)}
              className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-3 min-w-0">
                <span className="text-xs font-semibold uppercase tracking-wide text-gray-400 shrink-0">
                  Output
                </span>
                {/* Preview only shown when collapsed — hidden when expanded since full content is visible below */}
                {!outputOpen && (
                  <span className="text-xs text-gray-500 truncate">
                    {entry?.trace.outputs?.answer}
                  </span>
                )}
              </div>
              {/* Maximize2 = expand (collapsed state), Minimize2 = collapse (expanded state) */}
              {outputOpen ? (
                <Minimize2 className="w-4 h-4 text-gray-400 shrink-0" />
              ) : (
                <Maximize2 className="w-4 h-4 text-gray-400 shrink-0" />
              )}
            </button>
            {outputOpen && (
              <div onMouseUp={handleMouseUp}>
                <JsonViewer value={entry?.trace.outputs} path="outputs" highlights={highlights} />
              </div>
            )}
          </div>
        </div>

        <RubricSidebar
          queueId={queueId!}
          feedbackMap={feedbackMap}
          isFeedbackLoading={isFeedbackLoading}
          onSubmit={submitFeedback}
          pendingSpan={pendingSpan}
          pendingText={pendingText}
          overlapWarning={overlapWarning}
          onClearSpan={clearSpan}
        />
      </div>
    </div>
  );
}
