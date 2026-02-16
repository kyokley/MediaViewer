import { useEffect, useState } from "react";
import { apiClient } from "../utils/api";
import { VideoProgress } from "../types/api";
import { usePagination } from "../context/PaginationContext";
import ErrorAlert from "../components/ErrorAlert";
import LoadingSpinner from "../components/LoadingSpinner";
import { PaginationControls } from "../components/PaginationControls";

export function VideoProgressPage() {
  const { currentPage, setCurrentPage, total, setTotal } = usePagination();
  const [videoProgress, setVideoProgress] = useState<VideoProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const limit = 20;

  useEffect(() => {
    const fetchProgress = async () => {
      try {
        setLoading(true);
        setError(null);
         const response = await apiClient.get("/video-progress/", {
           params: { limit, offset: currentPage * limit },
         });
        setVideoProgress(response.data.data || []);
        setTotal(response.data.pagination?.total || 0);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch video progress"
        );
        setVideoProgress([]);
      } finally {
        setLoading(false);
      }
    };

    fetchProgress();
  }, [currentPage, limit, setTotal]);

  const handleDeleteProgress = async (hashedFilename: string) => {
    if (window.confirm("Are you sure you want to delete this progress?")) {
      try {
         await apiClient.delete(
           `/video-progress/${hashedFilename}/`
         );
        setVideoProgress(
          videoProgress.filter((v) => v.hashed_filename !== hashedFilename)
        );
        setTotal(total - 1);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to delete progress"
        );
      }
    }
  };

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    }
    return `${minutes}m ${secs}s`;
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Video Progress
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          View and manage your watched video progress
        </p>
      </div>

      {error && <ErrorAlert message={error} />}

      {/* Progress List */}
      {loading ? (
        <LoadingSpinner />
      ) : videoProgress.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg">
          <p className="text-gray-600 dark:text-gray-400">
            No video progress tracked yet.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {videoProgress.map((progress) => (
            <div
              key={progress.id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {progress.movie_name || progress.media_file_name || "Unknown"}
                    </h3>
                  </div>
                  <div className="mt-3 space-y-1">
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Progress: <span className="font-medium">{formatTime(progress.offset)}</span>
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Last watched:{" "}
                      <span className="font-medium">
                        {new Date(progress.date_edited).toLocaleString()}
                      </span>
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleDeleteProgress(progress.hashed_filename)}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition"
                >
                  Clear
                </button>
              </div>

              {/* Progress Bar */}
              <div className="mt-4">
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${Math.min((progress.offset / 3600) * 10, 100)}%` }}
                  />
                </div>
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
  );
}
