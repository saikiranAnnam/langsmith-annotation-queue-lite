import { ChevronRight, Folder } from "lucide-react";
import { Link } from "react-router-dom";
import { useProjects } from "../hooks/useApi";

export function ProjectsPage() {
  const { projects, isLoading, isError } = useProjects();

  if (isError) {
    return (
      <div className="p-8 text-center text-red-600">
        <p className="font-semibold">Failed to load projects.</p>
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
    return <div className="p-8 text-center">Loading projects...</div>;

  return (
    <div className="max-w-4xl mx-auto p-8 ">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Tracing Projects</h1>
        {/* TODO: Add create project button */}
      </div>

      <div className="grid gap-4 w-[800px]">
        {projects.length === 0 ? (
          <div className="p-8 text-center bg-gray-50 rounded-lg border border-gray-200 text-gray-500">
            No projects found.
          </div>
        ) : (
          projects.map((project) => (
            <Link
              key={project.id}
              to={`/projects/${project.id}`}
              className="block bg-white p-6 rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                    <Folder className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {project.name}
                    </h3>
                    <p className="text-sm text-gray-500">
                      Created{" "}
                      {new Date(project.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-400" />
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
