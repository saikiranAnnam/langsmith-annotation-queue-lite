import { useParams } from "react-router-dom";
import { useQueueSession } from "../hooks/useQueueSession";
import { useQueue } from "../hooks/useApi";

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
      {/* Header: queue name on the left, action buttons on the right */}
      <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-wide">Queue</p>
          <h2 className="font-semibold text-gray-900">{queue?.name ?? "..."}</h2>
        </div>
        <div className="flex items-center gap-3">
          {/* Skip requeues the entry so another reviewer can pick it up later */}
          <button
            onClick={skipEntry}
            className="px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Skip
          </button>
          {/* Complete marks the entry done and immediately loads the next one */}
          <button
            onClick={completeEntry}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            Complete & Next
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex gap-4 p-6 overflow-auto items-start">
          {/* Input panel — what was sent to the model by the user */}
          <div className="flex-1 flex flex-col gap-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">
              Input
            </p>
            <pre
              className="bg-white border border-gray-200 rounded-lg p-4 text-xs font-mono overflow-auto whitespace-pre-wrap max-h-[70vh]"
              dangerouslySetInnerHTML={{ __html: highlightJson(entry?.trace.inputs) }}
            />
          </div>
          {/* Output panel - what the model responded with */}
          <div className="flex-1 flex flex-col gap-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">
              Output
            </p>
            <pre
              className="bg-white border border-gray-200 rounded-lg p-4 text-xs font-mono overflow-auto whitespace-pre-wrap max-h-[70vh]"
              dangerouslySetInnerHTML={{ __html: highlightJson(entry?.trace.outputs) }}
            />
          </div>
        </div>

        <div className="w-72 border-l border-gray-200 bg-white p-4 text-sm text-gray-400">
          Rubric sidebar coming soon
        </div>
      </div>
    </div>
  );
}
