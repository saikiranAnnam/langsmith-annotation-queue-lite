import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { API_BASE, fetcher, postData } from "../lib/api";
import type {
  FeedbackCreate,
  Queue,
  QueueEntry,
  QueueRubricItem,
  TracingProject,
  Trace,
} from "../types";

export function useProjects() {
  const { data, error, isLoading } = useSWR<TracingProject[]>(
    `${API_BASE}/projects`,
    fetcher
  );
  return {
    projects: data || [],
    isLoading,
    isError: error,
  };
}

export function useProject(projectId: string | null) {
  const { data, error, isLoading } = useSWR<TracingProject>(
    projectId ? `${API_BASE}/projects/${projectId}` : null,
    fetcher
  );
  return {
    project: data,
    isLoading,
    isError: error,
  };
}

export function useProjectTraces(projectId: string | null) {
  // Note: The backend has a generic query endpoint, but let's see if there's a direct list.
  // README says POST /traces/query.
  // We'll implement a custom fetcher for this or just use SWR with a key that implies the query.
  // For simplicity, let's assume we want to query all traces for a project.
  
  const key = projectId ? `${API_BASE}/traces/query?project=${projectId}` : null;
  
  const { data, error, isLoading } = useSWR<Trace[]>(
    key,
    async () => {
      if (!projectId) return [];
      return postData<Trace[]>(`${API_BASE}/traces/query`, { project_id: projectId });
    }
  );

  return {
    traces: data || [],
    isLoading,
    isError: error,
  };
}

export function useQueues() {
  const { data, error, isLoading } = useSWR<Queue[]>(
    `${API_BASE}/queues`,
    fetcher
  );
  return {
    queues: data || [],
    isLoading,
    isError: error,
  };
}

export function useQueue(queueId: string | null) {
  const { data, error, isLoading } = useSWR<Queue>(
    queueId ? `${API_BASE}/queues/${queueId}` : null,
    fetcher
  );
  return {
    queue: data,
    isLoading,
    isError: error,
  };
}

export function useQueueRubric(queueId: string | null) {
  const { data, error, isLoading } = useSWR<QueueRubricItem[]>(
    queueId ? `${API_BASE}/queues/${queueId}/rubric` : null,
    fetcher
  );
  return {
    rubric: data || [],
    isLoading,
    isError: error,
  };
}

export function useQueueNextEntry(queueId: string | null) {
  const { data, error, isLoading, mutate } = useSWR<QueueEntry | null>(
    queueId ? `${API_BASE}/queues/${queueId}/entries/next` : null,
    async (url) => {
        try {
            return await fetcher(url);
        } catch (e: any) {
            if (e.status === 404 || e.status === 204) return null;
            throw e;
        }
    },
    {
      revalidateOnFocus: false, // Don't re-fetch when focusing window to avoid skipping items if not intended
      shouldRetryOnError: false,
    }
  );
  return {
    entry: data,
    isLoading,
    isError: error,
    mutate, // To refresh when we skip or complete
  };
}

export function useSubmitFeedback() {
    return useSWRMutation(
        `${API_BASE}/feedback/batch`,
        async (url, { arg }: { arg: FeedbackCreate[] }) => {
            return postData(url, arg);
        }
    );
}

export function useCompleteQueueEntry() {
    return useSWRMutation(
        // Key is dynamic based on call, so we use a generic key or null
        // But useSWRMutation needs a key.
        // We'll use a stable key and pass the dynamic part in arg or construct url in fetcher.
        // Let's just use a generic key.
        "complete-entry", 
        async (_, { arg }: { arg: { queueId: string; entryId: string } }) => {
            return postData(`${API_BASE}/queues/${arg.queueId}/entries/${arg.entryId}/complete`, {});
        }
    );
}

