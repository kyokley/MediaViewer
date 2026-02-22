import { useState } from 'react'
import Layout from '../components/Layout'
import MovieCard from '../components/MovieCard'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import { useMovies, useGenres } from '../hooks/useMovies'

export default function MoviesPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [selectedGenre, setSelectedGenre] = useState<number | undefined>()
  const [sortBy, setSortBy] = useState('date_added')

  const limit = 20
  const { movies, isLoading, error, total } = useMovies(
    page,
    limit,
    debouncedSearch,
    selectedGenre,
    sortBy
  )
  const { genres } = useGenres()
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

  // Handle genre filter change
  const handleGenreChange = (genreId: number | undefined) => {
    setSelectedGenre(genreId)
    setPage(1) // Reset to first page on filter change
  }

  // Handle sort change
  const handleSortChange = (value: string) => {
    setSortBy(value)
    setPage(1) // Reset to first page on sort change
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold mb-6" style={{ color: 'var(--text-primary)' }}>
            Movies
          </h1>

          {/* Search Bar and Sort Dropdown */}
          <div className="flex gap-4 mb-4">
            <input
              type="text"
              placeholder="Search movies..."
              value={search}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="flex-1 px-4 py-3 rounded-lg border focus:ring-2 outline-none transition"
              style={{
                backgroundColor: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                borderColor: 'var(--border-primary)',
              }}
            />

            <select
              value={sortBy}
              onChange={(e) => handleSortChange(e.target.value)}
              className="px-4 py-3 rounded-lg border focus:ring-2 outline-none transition cursor-pointer"
              style={{
                backgroundColor: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                borderColor: 'var(--border-primary)',
              }}
            >
              <option value="date_added">Recently Added</option>
              <option value="name">Name (A-Z)</option>
              <option value="release_date">Release Date</option>
            </select>
          </div>

          {/* Genre Filter */}
          {genres.length > 0 && (
            <div className="mt-4">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                  Filter by Genre:
                </span>
                <button
                  onClick={() => handleGenreChange(undefined)}
                  className="px-3 py-1 rounded-full text-sm transition"
                  style={{
                    backgroundColor: selectedGenre === undefined ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                    color: selectedGenre === undefined ? '#ffffff' : 'var(--text-secondary)',
                  }}
                >
                  All
                </button>
                {genres.slice(0, 10).map((genre) => (
                  <button
                    key={genre.id}
                    onClick={() => handleGenreChange(genre.id)}
                    className="px-3 py-1 rounded-full text-sm transition"
                    style={{
                      backgroundColor: selectedGenre === genre.id ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                      color: selectedGenre === genre.id ? '#ffffff' : 'var(--text-secondary)',
                    }}
                  >
                    {genre.name}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && <ErrorAlert message={error} />}

        {/* Movies Grid */}
        {isLoading ? (
          <LoadingSpinner />
        ) : movies.length === 0 ? (
          <div className="text-center py-12" style={{ color: 'var(--text-secondary)' }}>
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
                className="px-4 py-2 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                style={{
                  backgroundColor: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                }}
              >
                Previous
              </button>

              <span style={{ color: 'var(--text-secondary)' }}>
                Page {page} of {totalPages}
              </span>

              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                style={{
                  backgroundColor: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                }}
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
