import clsx from "clsx";
import { Folder, ListChecks } from "lucide-react";
import {
  BrowserRouter,
  NavLink,
  Outlet,
  Route,
  Routes,
} from "react-router-dom";
import { AnnotationQueuePage } from "./pages/AnnotationQueuePage";
import { ProjectDetailsPage } from "./pages/ProjectDetailsPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { QueuesPage } from "./pages/QueuesPage";

function Layout() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 h-14 flex items-center justify-between shadow-sm z-20">
        <div className="flex items-center gap-8">
          <span className="font-bold text-xl tracking-tight text-gray-900">
            LangSmith Annotation
          </span>
          <div className="flex items-center gap-1">
            <NavLink
              to="/projects"
              className={({ isActive }) =>
                clsx(
                  "px-3 py-2 rounded-md text-sm font-medium flex items-center gap-2 transition-colors",
                  isActive
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                )
              }
            >
              <Folder className="w-4 h-4" />
              Projects
            </NavLink>
            <NavLink
              to="/queues"
              className={({ isActive }) =>
                clsx(
                  "px-3 py-2 rounded-md text-sm font-medium flex items-center gap-2 transition-colors",
                  isActive
                    ? "bg-purple-50 text-purple-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                )
              }
            >
              <ListChecks className="w-4 h-4" />
              Queues
            </NavLink>
          </div>
        </div>
      </nav>
      <div className="flex-1 overflow-hidden flex flex-col">
        <Outlet />
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<ProjectsPage />} />{" "}
          {/* Default to projects */}
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/projects/:projectId" element={<ProjectDetailsPage />} />
          <Route path="/queues" element={<QueuesPage />} />
          <Route
            path="/queues/:queueId/annotate"
            element={<AnnotationQueuePage />}
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
