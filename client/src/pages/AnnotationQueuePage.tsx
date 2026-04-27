import { useState, useEffect, useRef } from "react";
import { useParams } from "react-router-dom";
import { Maximize2, Minimize2, CircleCheckBig, AlertCircle, Loader2, Keyboard, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { useQueueSession } from "../hooks/useQueueSession";
import { useQueue } from "../hooks/useApi";
import { useFeedbackManager } from "../hooks/useFeedbackManager";
import { RubricSidebar } from "../components/RubricSidebar";
import type { RubricSidebarHandle } from "../components/RubricSidebar";
import { JsonViewer } from "../components/JsonViewer";
import { useSpanSelection } from "../hooks/useSpanSelection";
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts";

const SHORTCUT_LEGEND = [
  { key: "1 – 9", desc: "Set score (0.1 – 0.9)" },
  { key: "0", desc: "Set score 1.0" },
  { key: "Enter", desc: "Submit active rubric item" },
  { key: "Tab", desc: "Cycle to next rubric item" },
  { key: "N", desc: "Complete & next entry" },
  { key: "S", desc: "Skip entry" },
  { key: "?", desc: "Toggle this legend" },
];

export function AnnotationQueuePage() {
  const { queueId } = useParams<{ queueId: string }>();
  const { queue } = useQueue(queueId ?? null);
  // useQueueSession handles fetching the next entry and reserving it on the backend
  const { entry, isLoading, isEmpty, isError, completeEntry, skipEntry, refresh } =
    useQueueSession(queueId!);

  const [isActioning, setIsActioning] = useState(false);
  const [showLegend, setShowLegend] = useState(false);

  const { feedbackMap, isFeedbackLoading, submitFeedback } = useFeedbackManager(
    entry?.trace_id ?? null
  );

  // Feedback records with span selections — passed to JsonViewer to render
  // per-rubric-item highlights on the relevant trace output fields.
  const highlights = Array.from(feedbackMap.values()).filter(
    (f) => f.span_path != null
  );

  const { pendingSpan, pendingText, overlapWarning, crossFieldWarning, clearSpan, handleMouseUp } =
    useSpanSelection(highlights);

  // Clear any pending span when the reviewer moves to a new entry so a span
  // selected on entry A cannot be accidentally saved against entry B's feedback.
  useEffect(() => {
    clearSpan();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entry?.trace_id]);

  // Both panels expanded by default so reviewers see the full content on load
  const [inputOpen, setInputOpen] = useState(true);
  const [outputOpen, setOutputOpen] = useState(true);

  const sidebarRef = useRef<RubricSidebarHandle>(null);

  // Stable refs so toast retry actions always call the latest handler version.
  const handleCompleteRef = useRef<() => Promise<void>>(async () => {});
  const handleSkipRef = useRef<() => Promise<void>>(async () => {});

  const handleComplete = async () => {
    if (isActioning) return;
    try {
      setIsActioning(true);
      await completeEntry();
    } catch {
      toast.error("Failed to complete entry", {
        action: { label: "Retry", onClick: () => handleCompleteRef.current() },
      });
    } finally {
      setIsActioning(false);
    }
  };
  handleCompleteRef.current = handleComplete;

  const handleSkip = async () => {
    if (isActioning) return;
    try {
      setIsActioning(true);
      await skipEntry();
    } catch {
      toast.error("Failed to skip entry", {
        action: { label: "Retry", onClick: () => handleSkipRef.current() },
      });
    } finally {
      setIsActioning(false);
    }
  };
  handleSkipRef.current = handleSkip;

  useKeyboardShortcuts(
    {
      onScore: (score) => sidebarRef.current?.setScore(score),
      onSubmitActive: () => sidebarRef.current?.submitActive(),
      onCycleNext: () => sidebarRef.current?.cycleNext(),
      onComplete: handleComplete,
      onSkip: handleSkip,
      onToggleLegend: () => setShowLegend((v) => !v),
    },
    !entry || isActioning
  );

  // Still waiting for the first entry to come back from the backend
  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="bg-white flex items-center shrink-0 h-16 border-b border-gray-200 px-6 gap-4">
          <div className="flex flex-col gap-1.5">
            <div className="h-2.5 w-12 bg-gray-100 rounded animate-pulse" />
            <div className="h-4 w-36 bg-gray-100 rounded animate-pulse" />
          </div>
        </div>
        <div className="flex-1 flex overflow-hidden">
          <div className="flex-1 p-6 flex flex-col gap-4">
            <div className="h-44 bg-gray-100 rounded-lg animate-pulse" />
            <div className="h-44 bg-gray-100 rounded-lg animate-pulse" />
          </div>
          <div className="w-[30%] min-w-72 border-l border-gray-200 bg-gray-50 p-4 flex flex-col gap-3">
            <div className="h-14 bg-gray-100 rounded-xl animate-pulse" />
            <div className="h-14 bg-gray-100 rounded-xl animate-pulse" />
            <div className="h-14 bg-gray-100 rounded-xl animate-pulse" />
          </div>
        </div>
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
      <div className="flex-1 flex flex-col items-center justify-center gap-5">
        <CircleCheckBig className="w-14 h-14 text-green-400" />
        <div className="text-center">
          <p className="text-xl font-semibold text-gray-900">Queue complete</p>
          <p className="text-sm text-gray-500 mt-1">All entries have been reviewed.</p>
        </div>
        <button
          onClick={refresh}
          className="flex items-center gap-2 h-9 px-4 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-all"
        >
          <RefreshCw className="w-4 h-4" />
          Check for new entries
        </button>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Keyboard shortcut legend overlay */}
      {showLegend && (
        <div
          className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center"
          onClick={() => setShowLegend(false)}
        >
          <div
            className="bg-white rounded-xl shadow-xl p-6 w-80"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-900">Keyboard Shortcuts</h3>
              <button
                onClick={() => setShowLegend(false)}
                className="text-gray-400 hover:text-gray-600 text-lg leading-none"
              >
                ✕
              </button>
            </div>
            <div className="flex flex-col gap-2.5">
              {SHORTCUT_LEGEND.map(({ key, desc }) => (
                <div key={key} className="flex items-center justify-between gap-4">
                  <span className="text-xs text-gray-500">{desc}</span>
                  <kbd className="shrink-0 text-[10px] font-mono font-semibold text-gray-600 bg-gray-100 border border-gray-300 rounded px-1.5 py-0.5">
                    {key}
                  </kbd>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Two-column header mirroring the content layout below */}
      <div className="bg-white flex items-center shrink-0 h-16">
        {/* Left column — aligns with the annotation/input-output panel */}
        <div className="flex-1 flex items-center justify-between px-6 h-full border-b border-gray-200">
          <div>
            <p className="text-[10px] font-medium text-gray-400 uppercase tracking-widest">Queue</p>
            <p className="text-base font-semibold text-gray-900 leading-snug">{queue?.name ?? "..."}</p>
          </div>
          <div className="flex items-center gap-2.5">
            {queue && (
              <span className="h-8 inline-flex items-center gap-1 px-3 text-xs font-semibold text-green-700 bg-green-50 border border-green-200 rounded-md">
                <span className="text-green-900">{queue.total_count - queue.pending_count}</span>
                <span className="text-green-500">/</span>
                <span className="text-green-900">{queue.total_count}</span>
                <span className="text-green-600 ml-0.5">reviewed</span>
              </span>
            )}
            <button
              onClick={() => setShowLegend((v) => !v)}
              title="Keyboard shortcuts (?)"
              className="h-8 w-8 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
            >
              <Keyboard className="w-4 h-4" />
            </button>
            {/* Skip requeues the entry so another reviewer can pick it up later */}
            <button
              disabled={isActioning}
              onClick={handleSkip}
              className="h-8 flex items-center gap-2 px-3 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150"
            >
              {isActioning ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  Skip
                  <kbd className="inline-flex items-center justify-center w-4 h-4 text-[10px] font-bold font-mono text-gray-400 bg-gray-100 border border-gray-300 rounded">
                    S
                  </kbd>
                </>
              )}
            </button>

            {/* Complete marks the entry done and immediately loads the next one */}
            <button
              disabled={isActioning}
              onClick={handleComplete}
              className="h-8 flex items-center gap-2 px-3 text-sm font-semibold text-white bg-green-600 rounded-md shadow-sm hover:bg-green-700 active:bg-green-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150"
            >
              {isActioning ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Working...
                </>
              ) : (
                <>
                  <CircleCheckBig className="w-3.5 h-3.5 shrink-0" />
                  Complete & Next
                  <kbd className="inline-flex items-center justify-center w-4 h-4 text-[10px] font-bold font-mono text-green-200 bg-green-700 border border-green-500 rounded">
                    N
                  </kbd>
                </>
              )}
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
          {/* Cross-field selection guidance — shown when reviewer drags across field boundaries */}
          {crossFieldWarning && (
            <div className="flex items-center gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              <AlertCircle className="w-3.5 h-3.5 shrink-0" />
              Please select within a single field to attach a highlight.
            </div>
          )}

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
          ref={sidebarRef}
          queueId={queueId!}
          feedbackMap={feedbackMap}
          isFeedbackLoading={isFeedbackLoading}
          onSubmit={submitFeedback}
          pendingSpan={pendingSpan}
          pendingText={pendingText}
          overlapWarning={overlapWarning}
          onClearSpan={clearSpan}
          onOpenLegend={() => setShowLegend(true)}
        />
      </div>
    </div>
  );
}
