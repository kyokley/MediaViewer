import Layout from '../components/Layout'
import MovieCard from '../components/MovieCard'
import TVCard from '../components/TVCard'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import { useMovies } from '../hooks/useMovies'
import { useTV } from '../hooks/useTV'

export default function HomePage() {
  const { movies, isLoading: moviesLoading, error: moviesError } = useMovies(1, 8)
  const { shows, isLoading: showsLoading, error: showsError } = useTV(1, 8)

  return (
    <Layout>
      <div className="space-y-12">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Welcome to MediaViewer</h1>
          <p className="text-gray-400">
            Discover and manage your favorite movies and TV shows
          </p>
        </div>

        {/* Featured Movies */}
        <section>
          <h2 className="text-2xl font-bold text-white mb-6">Featured Movies</h2>

          {moviesError && <ErrorAlert message={moviesError} />}

          {moviesLoading ? (
            <LoadingSpinner />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {movies.map((movie) => (
                <MovieCard key={movie.id} movie={movie} />
              ))}
            </div>
          )}
        </section>

        {/* Featured TV Shows */}
        <section>
          <h2 className="text-2xl font-bold text-white mb-6">Featured TV Shows</h2>

          {showsError && <ErrorAlert message={showsError} />}

          {showsLoading ? (
            <LoadingSpinner />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {shows.map((show) => (
                <TVCard key={show.id} show={show} />
              ))}
            </div>
          )}
        </section>
      </div>
    </Layout>
  )
}
