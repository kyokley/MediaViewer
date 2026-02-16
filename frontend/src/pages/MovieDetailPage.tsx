import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import { apiClient } from '../utils/api'
import { Movie } from '../types/api'

export default function MovieDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [movie, setMovie] = useState<Movie | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchMovie = async () => {
      if (!id) {
        setError('Movie ID is required')
        setIsLoading(false)
        return
      }

      setIsLoading(true)
      setError(null)

      try {
        const response = await apiClient.get(`/movies/${id}/`)
        setMovie(response.data.data)
      } catch (err: any) {
        setError(
          err.response?.data?.error?.message ||
            'Failed to fetch movie details'
        )
      } finally {
        setIsLoading(false)
      }
    }

    fetchMovie()
  }, [id])

  if (isLoading) {
    return (
      <Layout>
        <LoadingSpinner />
      </Layout>
    )
  }

  if (error || !movie) {
    return (
      <Layout>
        {error && <ErrorAlert message={error} />}
        <button
          onClick={() => navigate('/movies')}
          className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
        >
          Back to Movies
        </button>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row gap-8 mb-12">
          {/* Poster */}
          <div className="flex-shrink-0 md:w-1/3">
            {movie.poster_image_url ? (
              <img
                src={movie.poster_image_url}
                alt={movie.title || movie.name}
                className="w-full rounded-lg shadow-lg"
              />
            ) : (
              <div className="w-full bg-gray-800 rounded-lg h-96 flex items-center justify-center text-gray-500">
                No poster available
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex-1">
            <h1 className="text-4xl font-bold text-white mb-2">
              {movie.title || movie.name}
            </h1>

            {movie.release_date && (
              <p className="text-gray-400 text-lg mb-4">
                {new Date(movie.release_date).getFullYear()}
              </p>
            )}

            {/* Genres */}
            {movie.genres && movie.genres.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-300 mb-2">Genres</h3>
                <div className="flex flex-wrap gap-2">
                  {movie.genres.map((genre) => (
                    <span
                      key={genre.id}
                      className="bg-gray-700 text-gray-300 px-3 py-1 rounded-full text-sm"
                    >
                      {genre.name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Description */}
            {movie.description && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-300 mb-2">Synopsis</h3>
                <p className="text-gray-400 leading-relaxed">{movie.description}</p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-4">
              <button className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition">
                Watch Now
              </button>
              <button className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition">
                Add to Collection
              </button>
            </div>
          </div>
        </div>

        {/* Back Button */}
        <button
          onClick={() => navigate('/movies')}
          className="text-blue-400 hover:text-blue-300 transition"
        >
          ← Back to Movies
        </button>
      </div>
    </Layout>
  )
}
