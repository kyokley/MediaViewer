import { useEffect, useState } from "react";
import { apiClient } from "../utils/api";
import { Comment } from "../types/api";

export function useComments(limit: number = 20, offset: number = 0) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchComments = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await apiClient.get("/comments/", {
          params: { limit, offset },
        });
        setComments(response.data.data || []);
        setTotal(response.data.pagination?.total || 0);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch comments"
        );
        setComments([]);
      } finally {
        setLoading(false);
      }
    };

    fetchComments();
  }, [limit, offset]);

  const createComment = async (data: Record<string, unknown>): Promise<Comment | null> => {
    try {
      const response = await apiClient.post("/comments/", data);
      // Add new comment to the beginning of the list
      setComments([response.data, ...comments]);
      setTotal(total + 1);
      return response.data;
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create comment"
      );
      return null;
    }
  };

  const updateComment = async (
    commentId: number,
    data: Record<string, unknown>
  ): Promise<Comment | null> => {
    try {
      const response = await apiClient.put(
        `/comments/${commentId}/`,
        data
      );
      // Update comment in the list
      setComments(
        comments.map((c) => (c.id === commentId ? response.data : c))
      );
      return response.data;
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update comment"
      );
      return null;
    }
  };

  const deleteComment = async (commentId: number): Promise<boolean> => {
    try {
      await apiClient.delete(`/comments/${commentId}/`);
      setComments(comments.filter((c) => c.id !== commentId));
      setTotal(total - 1);
      return true;
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete comment"
      );
      return false;
    }
  };

  return {
    comments,
    total,
    loading,
    error,
    createComment,
    updateComment,
    deleteComment,
  };
}
