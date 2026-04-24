import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { API_BASE, fetcher, postData } from "../lib/api";
import type { QueueEntry } from "../types";

export function useQueueSession(queueId: string) {
  // Fetching this URL also reserves the entry on the backend (sets it to in_progress).
  // Two users hitting this at the same time will get different entries using the database's FOR UPDATE SKIP LOCKED.
  const swrKey = `${API_BASE}/queues/${queueId}/entries/next`;

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
      revalidateOnFocus: false, // don't reserve a new entry just because the user switched tabs
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
    // Clear the cache and re-fetch — this automatically reserves the next pending entry
    mutate(undefined, { revalidate: true });
  };

  const skipEntry = async () => {
    if (!entry) return;
    // Requeue puts this entry back to pending so another reviewer can pick it up
    await triggerRequeue({ queueId, entryId: entry.id });
    mutate(undefined, { revalidate: true });
  };

  return {
    entry: entry ?? null,
    isLoading,
    // isEmpty is true only after loading finishes with no error and genuinely nothing left
    isEmpty: !isLoading && !loadError && entry === null,
    isError: !!loadError,
    completeEntry,
    skipEntry,
  };
}
