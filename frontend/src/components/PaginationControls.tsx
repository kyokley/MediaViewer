interface PaginationControlsProps {
  currentPage: number
  totalPages: number
  onPreviousClick: () => void
  onNextClick: () => void
}

export function PaginationControls({
  currentPage,
  totalPages,
  onPreviousClick,
  onNextClick,
}: PaginationControlsProps) {
  return totalPages > 1 ? (
    <div className="flex items-center justify-center gap-2 pt-4">
      <button
        onClick={onPreviousClick}
        disabled={currentPage === 0}
        className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
      >
        Previous
      </button>
      <span className="text-sm text-gray-600 dark:text-gray-400">
        Page {currentPage + 1} of {totalPages}
      </span>
      <button
        onClick={onNextClick}
        disabled={currentPage >= totalPages - 1}
        className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
      >
        Next
      </button>
    </div>
  ) : null
}
