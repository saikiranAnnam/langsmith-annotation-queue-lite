import useSWR, { mutate as globalMutate } from "swr";
import useSWRMutation from "swr/mutation";
import { API_BASE, fetcher, postData } from "../lib/api";
import { getReviewerId } from "../lib/reviewerId";
import type { QueueEntry } from "../types";

export function useQueueSession(queueId: string) {
  // Fetching this URL also reserves the queue entry on the backend (sets it to in_progress).
  // Two reviewers hitting this concurrently get different entries via FOR UPDATE SKIP LOCKED.
  // reviewer_id ensures a refresh returns the same entry rather than reserving a new one.
  const swrKey = `${API_BASE}/queues/${queueId}/entries/next?reviewer_id=${getReviewerId()}`;

  const { data: entry, isLoading, error: loadError, mutate } = useSWR<QueueEntry | null>(
    swrKey,
    async (url) => {
      try {
        return await fetcher(url);
      } catch (e: any) {
        // 404 just means the queue is empty — that's a valid end state, not an error
        if (e.status === 404) return null;
        throw e;
      }
    },
    {
      revalidateOnFocus: false, // switching tabs would trigger a fetch, which also reserves an entry
      shouldRetryOnError: false,
    }
  );

  const { trigger: triggerComplete } = useSWRMutation(
    "complete-queue-entry",
    async (_, { arg }: { arg: { queueId: string; entryId: string } }) =>
      postData(`${API_BASE}/queues/${arg.queueId}/entries/${arg.entryId}/complete`, {})
  );

  const { trigger: triggerRequeue } = useSWRMutation(
    "requeue-entry",
    async (_, { arg }: { arg: { queueId: string; entryId: string } }) =>
      postData(`${API_BASE}/queues/${arg.queueId}/entries/${arg.entryId}/requeue`, {})
  );

  const completeEntry = async () => {
    if (!entry) return;
    await triggerComplete({ queueId, entryId: entry.id });
    // Clear the cache and re-fetch — this automatically reserves the next pending entry.
    // Also invalidate the queue detail so pending_count updates without a page refresh.
    mutate(undefined, { revalidate: true });
    globalMutate(`${API_BASE}/queues/${queueId}`);
  };

  const skipEntry = async () => {
    if (!entry) return;
    // Requeue puts this entry back to pending so another reviewer can pick it up
    await triggerRequeue({ queueId, entryId: entry.id });
    mutate(undefined, { revalidate: true });
    globalMutate(`${API_BASE}/queues/${queueId}`);
  };

  const refresh = () => mutate(undefined, { revalidate: true });

  return {
    entry: entry ?? null,
    isLoading,
    // isEmpty is true only after loading finishes with no error and genuinely nothing left
    isEmpty: !isLoading && !loadError && entry === null,
    isError: !!loadError,
    completeEntry,
    skipEntry,
    refresh,
  };
}
