import { useState } from "react";
import { useComments } from "../hooks/useComments";
import ErrorAlert from "../components/ErrorAlert";
import LoadingSpinner from "../components/LoadingSpinner";

export function CommentsPage() {
  const [currentPage, setCurrentPage] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const limit = 20;
  const {
    comments,
    total,
    loading,
    error,
    updateComment,
    deleteComment,
  } = useComments(limit, currentPage * limit);

  const handleUpdateComment = async (commentId: number) => {
    setSubmitting(true);
    const result = await updateComment(commentId, {
      viewed: true,
    });
    setSubmitting(false);

    if (result) {
      // Comment updated
    }
  };

  const handleDeleteComment = async (commentId: number) => {
    if (window.confirm("Are you sure you want to delete this comment?")) {
      await deleteComment(commentId);
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Comments
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          View and manage your comments on media
        </p>
      </div>

      {error && <ErrorAlert message={error} />}

      {/* Comments List */}
      {loading ? (
        <LoadingSpinner />
      ) : comments.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg">
          <p className="text-gray-600 dark:text-gray-400">No comments yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {comments.map((comment) => (
            <div
              key={comment.id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-3"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    {comment.user_username}
                    {comment.movie_name && ` on ${comment.movie_name}`}
                    {comment.media_file_name && ` (${comment.media_file_name})`}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    {new Date(comment.date_created).toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  {comment.viewed && (
                    <span className="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-100 dark:bg-blue-900 dark:text-blue-200 rounded">
                      Viewed
                    </span>
                  )}
                  {!comment.viewed && (
                    <button
                      onClick={() => handleUpdateComment(comment.id)}
                      disabled={submitting}
                      className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 disabled:opacity-50"
                    >
                      Mark Viewed
                    </button>
                  )}
                  <button
                    onClick={() => handleDeleteComment(comment.id)}
                    className="text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                  >
                    Delete
                  </button>
                </div>
              </div>

              <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                <p className="text-gray-700 dark:text-gray-300 text-sm">
                  Comment ID: {comment.id}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-4">
          <button
            onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
            disabled={currentPage === 0}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Page {currentPage + 1} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={currentPage >= totalPages - 1}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
