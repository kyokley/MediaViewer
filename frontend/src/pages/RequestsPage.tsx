import { useState } from "react";
import { useRequests } from "../hooks/useRequests";
import { usePagination } from "../context/PaginationContext";
import Layout from "../components/Layout";
import ErrorAlert from "../components/ErrorAlert";
import LoadingSpinner from "../components/LoadingSpinner";
import { PaginationControls } from "../components/PaginationControls";

export function RequestsPage() {
  const { currentPage, setCurrentPage, total, setTotal } = usePagination();
  const [newRequestName, setNewRequestName] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const limit = 20;
  const {
    requests,
    total: hookTotal,
    loading,
    error,
    createRequest,
    deleteRequest,
    voteForRequest,
    markRequestDone,
  } = useRequests(limit, currentPage * limit);

  // Sync total from hook to context
  if (hookTotal !== total) {
    setTotal(hookTotal);
  }

  const handleCreateRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRequestName.trim()) return;

    setSubmitting(true);
    const result = await createRequest(newRequestName.trim());
    setSubmitting(false);

    if (result) {
      setNewRequestName("");
      setShowForm(false);
      setCurrentPage(0); // Reset to first page
    }
  };

  const handleVote = async (requestId: number) => {
    await voteForRequest(requestId);
  };

  const handleMarkDone = async (requestId: number) => {
    await markRequestDone(requestId);
  };

  const handleDelete = async (requestId: number) => {
    if (window.confirm("Are you sure you want to delete this request?")) {
      await deleteRequest(requestId);
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <Layout>
      <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-white mb-6">
          Media Requests
        </h1>
        <p className="text-gray-400">
          Request new media to be added to the library. Vote for requests you want!
        </p>
      </div>

      {error && <ErrorAlert message={error} />}

      {/* Create Request Form */}
      {!showForm ? (
        <button
          onClick={() => setShowForm(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
        >
          + New Request
        </button>
      ) : (
        <form
          onSubmit={handleCreateRequest}
          className="bg-gray-800 rounded-lg shadow p-6 space-y-4"
        >
          <div>
            <label className="block text-sm font-medium text-gray-300">
              Request Name
            </label>
            <input
              type="text"
              value={newRequestName}
              onChange={(e) => setNewRequestName(e.target.value)}
              placeholder="e.g., 'Avatar 3' or 'The Last of Us Season 2'"
              className="mt-1 block w-full px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 outline-none transition placeholder-gray-400"
              disabled={submitting}
            />
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={submitting || !newRequestName.trim()}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400"
            >
              {submitting ? "Creating..." : "Create Request"}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowForm(false);
                setNewRequestName("");
              }}
              className="inline-flex items-center px-4 py-2 border border-gray-600 text-sm font-medium rounded-md text-gray-300 bg-gray-700 hover:bg-gray-600"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Requests List */}
      {loading ? (
        <LoadingSpinner />
      ) : requests.length === 0 ? (
        <div className="text-center py-12 bg-gray-800 rounded-lg">
          <p className="text-gray-400">No requests yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {requests.map((request) => (
            <div
              key={request.id}
              className="bg-gray-800 rounded-lg shadow p-6 space-y-4"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3
                    className={`text-lg font-semibold ${
                      request.done
                        ? "line-through text-gray-400"
                        : "text-white"
                    }`}
                  >
                    {request.name}
                  </h3>
                  <p className="text-sm text-gray-400 mt-1">
                    Requested by <span className="font-medium">{request.user_username}</span> on{" "}
                    {new Date(request.datecreated).toLocaleDateString()}
                  </p>
                </div>
                {request.done && (
                  <span className="px-3 py-1 text-sm font-medium text-green-200 bg-green-900 rounded-full">
                    Done
                  </span>
                )}
              </div>

              <div className="flex items-center gap-4 pt-4 border-t border-gray-700">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleVote(request.id)}
                    className="inline-flex items-center px-3 py-2 text-sm font-medium text-blue-400 hover:bg-blue-900/30 rounded"
                  >
                    👍 Vote
                  </button>
                  <span className="text-sm font-medium text-gray-300">
                    {request.vote_count} {request.vote_count === 1 ? "vote" : "votes"}
                  </span>
                </div>

                {!request.done && (
                  <button
                    onClick={() => handleMarkDone(request.id)}
                    className="inline-flex items-center px-3 py-2 text-sm font-medium text-green-400 hover:bg-green-900/30 rounded"
                  >
                    ✓ Mark Done
                  </button>
                )}

                <button
                  onClick={() => handleDelete(request.id)}
                  className="ml-auto inline-flex items-center px-3 py-2 text-sm font-medium text-red-400 hover:bg-red-900/30 rounded"
                >
                  🗑 Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      <PaginationControls
        currentPage={currentPage}
        totalPages={totalPages}
        onPreviousClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
        onNextClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
      />
    </div>
    </Layout>
  );
}
