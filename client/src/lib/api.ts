export const API_BASE = "http://localhost:8000";

export const fetcher = async (url: string) => {
  const res = await fetch(url);
  if (!res.ok) {
    const error = new Error("An error occurred while fetching the data.");
    console.error(`API Error fetching ${url}:`, res.status, res.statusText);

    try {
      // @ts-expect-error - We don't know the type of the info property.
      error.info = await res.json();
    } catch (e) {
      console.error("Failed to parse error response JSON:", e);
      // @ts-expect-error - We don't know the type of the info property.
      error.info = { message: res.statusText };
    }

    // @ts-expect-error - We don't know the type of the status property.
    error.status = res.status;
    throw error;
  }
  return res.json();
};

export async function postData<T>(url: string, data: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = new Error("An error occurred while posting the data.");
    console.error(`API Error posting to ${url}:`, res.status, res.statusText);

    try {
      // @ts-expect-error - We don't know the type of the info property.
      error.info = await res.json();
    } catch (e) {
      console.error("Failed to parse error response JSON:", e);
      // @ts-expect-error - We don't know the type of the info property.
      error.info = { message: res.statusText };
    }

    // @ts-expect-error - We don't know the type of the status property.
    error.status = res.status;
    throw error;
  }

  return res.json();
}

export async function deleteData(url: string) {
  const res = await fetch(url, {
    method: "DELETE",
  });

  if (!res.ok) {
    const error = new Error("An error occurred while deleting the data.");
    console.error(`API Error deleting ${url}:`, res.status, res.statusText);

    try {
      // @ts-expect-error - We don't know the type of the info property.
      error.info = await res.json();
    } catch (e) {
      console.error("Failed to parse error response JSON:", e);
      // @ts-expect-error - We don't know the type of the info property.
      error.info = { message: res.statusText };
    }

    // @ts-expect-error - We don't know the type of the status property.
    error.status = res.status;
    throw error;
  }

  return res.json();
}
