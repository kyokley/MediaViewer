import { useState } from 'react'
import Layout from '../components/Layout'
import MovieCard from '../components/MovieCard'
import TVCard from '../components/TVCard'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import { useSearch } from '../hooks/useSearch'

type SearchType = 'all' | 'movie' | 'tv'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [searchType, setSearchType] = useState<SearchType>('all')
  const { search, results, isLoading, error } = useSearch()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    search(query, searchType)
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold text-white mb-6">Search</h1>

          {/* Search Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Search movies and TV shows..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="flex-1 px-4 py-3 bg-gray-800 text-white rounded-lg border border-gray-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 outline-none transition"
              />
              <button
                type="submit"
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition font-medium"
              >
                Search
              </button>
            </div>

            {/* Search Type Filter */}
            <div className="flex gap-2">
              {['all', 'movie', 'tv'].map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setSearchType(type as SearchType)}
                  className={`px-4 py-2 rounded-lg transition ${
                    searchType === type
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  {type === 'all' ? 'All' : type === 'movie' ? 'Movies' : 'TV Shows'}
                </button>
              ))}
            </div>
          </form>
        </div>

        {/* Error Message */}
        {error && <ErrorAlert message={error} />}

        {/* Loading State */}
        {isLoading && <LoadingSpinner />}

        {/* Results */}
        {results && (
          <div className="space-y-8">
            {/* Movies Results */}
            {results.movies.length > 0 && (
              <section>
                <h2 className="text-2xl font-bold text-white mb-6">
                  Movies ({results.movies.length})
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                  {results.movies.map((movie) => (
                    <MovieCard key={movie.id} movie={movie} />
                  ))}
                </div>
              </section>
            )}

            {/* TV Shows Results */}
            {results.tv.length > 0 && (
              <section>
                <h2 className="text-2xl font-bold text-white mb-6">
                  TV Shows ({results.tv.length})
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                  {results.tv.map((show) => (
                    <TVCard key={show.id} show={show} />
                  ))}
                </div>
              </section>
            )}

            {/* No Results */}
            {results.movies.length === 0 && results.tv.length === 0 && (
              <div className="text-center py-12 text-gray-400">
                No results found for "{query}"
              </div>
            )}
          </div>
        )}

        {/* Initial State */}
        {!results && !isLoading && (
          <div className="text-center py-12 text-gray-400">
            Enter a search query to get started
          </div>
        )}
      </div>
    </Layout>
  )
}
