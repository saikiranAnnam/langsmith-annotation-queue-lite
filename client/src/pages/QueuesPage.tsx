import { ChevronRight, ListChecks } from "lucide-react";
import { Link } from "react-router-dom";
import { useQueues } from "../hooks/useApi";

export function QueuesPage() {
  const { queues, isLoading, isError } = useQueues();

  if (isError) {
    return (
      <div className="p-8 text-center text-red-600">
        <p className="font-semibold">Failed to load queues.</p>
        <p className="text-sm mt-2">
          Please ensure the backend server is running on port 8000.
        </p>
        <p className="text-xs mt-1 text-gray-500 font-mono">
          {isError.message || JSON.stringify(isError)}
        </p>
      </div>
    );
  }

  if (isLoading)
    return <div className="p-8 text-center">Loading queues...</div>;

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Annotation Queues</h1>
        {/* TODO: Add create queue button */}
      </div>

      <div className="grid gap-4 w-[800px]">
        {queues.length === 0 ? (
          <div className="p-8 text-center bg-gray-50 rounded-lg border border-gray-200 text-gray-500">
            No queues found.
          </div>
        ) : (
          queues.map((queue) => (
            <Link
              key={queue.id}
              to={`/queues/${queue.id}/annotate`}
              className="block bg-white p-6 rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-50 text-purple-600 rounded-lg">
                    <ListChecks className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {queue.name}
                    </h3>
                    <p className="text-sm text-gray-500">
                      Created {new Date(queue.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-blue-600">
                    Start Annotating
                  </span>
                  <ChevronRight className="w-5 h-5 text-blue-600" />
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
