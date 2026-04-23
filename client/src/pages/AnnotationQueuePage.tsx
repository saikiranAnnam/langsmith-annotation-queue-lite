import { useState } from "react";
import { useParams } from "react-router-dom";
import { Maximize2, Minimize2, CircleCheckBig } from "lucide-react";
import { useQueueSession } from "../hooks/useQueueSession";
import { useQueue } from "../hooks/useApi";
import { useFeedbackManager } from "../hooks/useFeedbackManager";
import { RubricSidebar } from "../components/RubricSidebar";

// Turns a JSON value into syntax-highlighted HTML.
function highlightJson(value: unknown): string {
  const json = JSON.stringify(value, null, 2) ?? "";
  return json
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(
      /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
      (match) => {
        // a quoted string followed by ":" is a key, everything else is a value
        if (/^"/.test(match) && /:$/.test(match))
          return `<span class="text-blue-600 font-semibold">${match}</span>`;
        if (/^"/.test(match))
          return `<span class="text-green-600">${match}</span>`;
        if (/true|false/.test(match))
          return `<span class="text-purple-600">${match}</span>`;
        if (/null/.test(match))
          return `<span class="text-gray-400">${match}</span>`;
        // anything left is a number
        return `<span class="text-orange-500">${match}</span>`;
      }
    );
}

export function AnnotationQueuePage() {
  const { queueId } = useParams<{ queueId: string }>();
  const { queue } = useQueue(queueId ?? null);
  // useQueueSession handles fetching the next entry and reserving it on the backend
  const { entry, isLoading, isEmpty, completeEntry, skipEntry } =
    useQueueSession(queueId!);

  const { feedbackMap, submitFeedback } = useFeedbackManager(
    entry?.trace_id ?? null
  );

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
            {/* Skip requeues the entry so another reviewer can pick it up later */}
            <button
              onClick={skipEntry}
              className="h-8 px-4 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 hover:border-gray-400 transition-all duration-150"
            >
              Skip
            </button>
            {/* Complete marks the entry done and immediately loads the next one */}
            <button
              onClick={completeEntry}
              className="h-8 flex items-center gap-2 px-4 text-sm font-semibold text-white bg-green-600 rounded-md shadow-sm hover:bg-green-700 active:bg-green-800 transition-all duration-150"
            >
              <CircleCheckBig className="w-3.5 h-3.5 shrink-0" />
              Complete & Next
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
              <pre
                className="px-4 pb-4 text-xs font-mono overflow-auto whitespace-pre-wrap max-h-[40vh] border-t border-gray-100"
                dangerouslySetInnerHTML={{ __html: highlightJson(entry?.trace.inputs) }}
              />
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
              <pre
                className="px-4 pb-4 text-xs font-mono overflow-auto whitespace-pre-wrap max-h-[40vh] border-t border-gray-100"
                dangerouslySetInnerHTML={{ __html: highlightJson(entry?.trace.outputs) }}
              />
            )}
          </div>
        </div>

        <RubricSidebar
          queueId={queueId!}
          feedbackMap={feedbackMap}
          onSubmit={submitFeedback}
        />
      </div>
    </div>
  );
}
