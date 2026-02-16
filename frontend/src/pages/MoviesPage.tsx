import { useState } from 'react'
import Layout from '../components/Layout'
import MovieCard from '../components/MovieCard'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import { useMovies } from '../hooks/useMovies'

export default function MoviesPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')

  const limit = 20
  const { movies, isLoading, error, total } = useMovies(page, limit, debouncedSearch)
  const totalPages = Math.ceil(total / limit)

  // Debounce search
  const handleSearchChange = (value: string) => {
    setSearch(value)
    setPage(1) // Reset to first page on search
    const timer = setTimeout(() => {
      setDebouncedSearch(value)
    }, 500)
    return () => clearTimeout(timer)
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold text-white mb-6">Movies</h1>

          {/* Search Bar */}
          <input
            type="text"
            placeholder="Search movies..."
            value={search}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full px-4 py-3 bg-gray-800 text-white rounded-lg border border-gray-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 outline-none transition"
          />
        </div>

        {/* Error Message */}
        {error && <ErrorAlert message={error} />}

        {/* Movies Grid */}
        {isLoading ? (
          <LoadingSpinner />
        ) : movies.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            {debouncedSearch ? 'No movies found matching your search.' : 'No movies available.'}
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {movies.map((movie) => (
                <MovieCard key={movie.id} movie={movie} />
              ))}
            </div>

            {/* Pagination */}
            <div className="flex justify-center items-center gap-4 mt-8">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                Previous
              </button>

              <span className="text-gray-400">
                Page {page} of {totalPages}
              </span>

              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                Next
              </button>
            </div>
          </>
        )}
      </div>
    </Layout>
  )
}
