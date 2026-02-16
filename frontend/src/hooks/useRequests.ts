import { useEffect, useState } from "react";
import { apiClient } from "../utils/api";
import { Request } from "../types/api";

export function useRequests(limit: number = 20, offset: number = 0) {
  const [requests, setRequests] = useState<Request[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRequests = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await apiClient.get("/mediaviewer/api/v2/requests/", {
          params: { limit, offset },
        });
        setRequests(response.data.data || []);
        setTotal(response.data.pagination?.total || 0);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch requests"
        );
        setRequests([]);
      } finally {
        setLoading(false);
      }
    };

    fetchRequests();
  }, [limit, offset]);

  const createRequest = async (name: string): Promise<Request | null> => {
    try {
      const response = await apiClient.post("/mediaviewer/api/v2/requests/", {
        name,
      });
      return response.data;
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create request"
      );
      return null;
    }
  };

  const deleteRequest = async (requestId: number): Promise<boolean> => {
    try {
      await apiClient.delete(
        `/mediaviewer/api/v2/requests/${requestId}/`
      );
      setRequests(requests.filter((r) => r.id !== requestId));
      return true;
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete request"
      );
      return false;
    }
  };

  const voteForRequest = async (requestId: number): Promise<Request | null> => {
    try {
      const response = await apiClient.post(
        `/mediaviewer/api/v2/requests/${requestId}/vote/`
      );
      // Update the request in the list with new vote count
      setRequests(
        requests.map((r) =>
          r.id === requestId ? { ...r, vote_count: response.data.data.vote_count } : r
        )
      );
      return response.data.data;
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to vote for request"
      );
      return null;
    }
  };

  const markRequestDone = async (requestId: number): Promise<Request | null> => {
    try {
      const response = await apiClient.post(
        `/mediaviewer/api/v2/requests/${requestId}/done/`
      );
      // Update the request in the list
      setRequests(
        requests.map((r) =>
          r.id === requestId ? response.data.data : r
        )
      );
      return response.data.data;
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to mark request as done"
      );
      return null;
    }
  };

  return {
    requests,
    total,
    loading,
    error,
    createRequest,
    deleteRequest,
    voteForRequest,
    markRequestDone,
  };
}
