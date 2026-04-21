import { useParams, Link } from "react-router-dom";
import { useProject, useProjectTraces } from "../hooks/useApi";
import { ArrowLeft, Calendar, Clock } from "lucide-react";

export function ProjectDetailsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { project, isLoading: isLoadingProject } = useProject(projectId || null);
  const { traces, isLoading: isLoadingTraces } = useProjectTraces(projectId || null);

  if (isLoadingProject || isLoadingTraces) {
    return <div className="p-8 text-center">Loading details...</div>;
  }

  if (!project) {
    return <div className="p-8 text-center text-red-500">Project not found</div>;
  }

  return (
    <div className="max-w-6xl mx-auto p-8">
      <div className="mb-8">
        <Link to="/projects" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-900 mb-4">
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to Projects
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
        <div className="flex items-center gap-4 text-sm text-gray-500 mt-2">
            <span className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                Created {new Date(project.created_at).toLocaleDateString()}
            </span>
            <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                Modified {new Date(project.modified_at).toLocaleDateString()}
            </span>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
              <h2 className="font-semibold text-gray-700">Traces ({traces.length})</h2>
          </div>
          <div className="divide-y divide-gray-200">
              {traces.length === 0 ? (
                  <div className="p-8 text-center text-gray-500">No traces recorded yet.</div>
              ) : (
                  traces.map(trace => (
                      <div key={trace.id} className="p-4 hover:bg-gray-50 transition-colors">
                          <div className="flex justify-between items-start mb-2">
                              <div className="font-mono text-xs text-gray-500">{trace.id}</div>
                              <div className="text-xs text-gray-400">{new Date(trace.start_time).toLocaleString()}</div>
                          </div>
                          <div className="grid grid-cols-2 gap-4">
                              <div className="bg-gray-50 p-2 rounded border border-gray-100">
                                  <div className="text-xs font-medium text-gray-500 mb-1 uppercase">Input</div>
                                  <pre className="text-xs overflow-auto max-h-32 text-gray-800 whitespace-pre-wrap">
                                      {JSON.stringify(trace.inputs, null, 2)}
                                  </pre>
                              </div>
                              <div className="bg-gray-50 p-2 rounded border border-gray-100">
                                  <div className="text-xs font-medium text-gray-500 mb-1 uppercase">Output</div>
                                  <pre className="text-xs overflow-auto max-h-32 text-gray-800 whitespace-pre-wrap">
                                      {JSON.stringify(trace.outputs, null, 2)}
                                  </pre>
                              </div>
                          </div>
                      </div>
                  ))
              )}
          </div>
      </div>
    </div>
  );
}

