import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import VideoPlayer from '../components/VideoPlayer'
import AddToCollectionModal from '../components/AddToCollectionModal'
import { EpisodeList } from '../components/EpisodeList'
import { apiClient } from '../utils/api'
import { TVShow } from '../types/api'
import { useEpisodes } from '../hooks/useTV'

export default function TVShowDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [show, setShow] = useState<TVShow | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showPlayer, setShowPlayer] = useState(false)
  const [showAddToCollection, setShowAddToCollection] = useState(false)

  // Fetch episodes using the useEpisodes hook
  const {
    seasons,
    isLoading: episodesLoading,
    error: episodesError,
  } = useEpisodes(parseInt(id || '0'))

  useEffect(() => {
    const fetchShow = async () => {
      if (!id) {
        setError('TV Show ID is required')
        setIsLoading(false)
        return
      }

      setIsLoading(true)
      setError(null)

      try {
        const response = await apiClient.get(`/tv/${id}/`)
        setShow(response.data)
      } catch (err: any) {
        setError(
          err.response?.data?.error?.message ||
            'Failed to fetch TV show details'
        )
      } finally {
        setIsLoading(false)
      }
    }

    fetchShow()
  }, [id])

  if (isLoading) {
    return (
      <Layout>
        <LoadingSpinner />
      </Layout>
    )
  }

  if (error || !show) {
    return (
      <Layout>
        {error && <ErrorAlert message={error} />}
        <button
          onClick={() => navigate('/tv')}
          className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
        >
          Back to TV Shows
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
            {show.poster_image_url ? (
              <img
                src={show.poster_image_url}
                alt={show.title || show.name}
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
              {show.title || show.name}
            </h1>

            {show.first_air_date && (
              <p className="text-gray-400 text-lg mb-4">
                First aired: {new Date(show.first_air_date).getFullYear()}
              </p>
            )}

            {/* Genres */}
            {show.genres && show.genres.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-300 mb-2">Genres</h3>
                <div className="flex flex-wrap gap-2">
                  {show.genres.map((genre) => (
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
            {show.description && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-300 mb-2">Synopsis</h3>
                <p className="text-gray-400 leading-relaxed">{show.description}</p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-4">
              <button
                onClick={() => setShowPlayer(true)}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition"
              >
                Watch Now
              </button>
              <button
                onClick={() => setShowAddToCollection(true)}
                className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition"
              >
                Add to Collection
              </button>
            </div>
          </div>
        </div>

        {/* Episodes Section */}
        <EpisodeList
          seasons={seasons}
          isLoading={episodesLoading}
          error={episodesError}
          showName={show.name}
          onPlayEpisode={(episode) => {
            // TODO: Implement play specific episode
            console.log('Play episode:', episode)
          }}
        />

        {/* Back Button */}
        <button
          onClick={() => navigate('/tv')}
          className="text-blue-400 hover:text-blue-300 transition mt-8"
        >
          ← Back to TV Shows
        </button>
      </div>

      {/* Video Player Modal */}
      {showPlayer && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-4xl">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-white text-lg font-semibold">
                Now Playing: {show?.title || show?.name}
              </h2>
              <button
                onClick={() => setShowPlayer(false)}
                className="text-gray-400 hover:text-white text-2xl transition"
              >
                ✕
              </button>
            </div>
            <VideoPlayer
              mediaId={parseInt(id!)}
              mediaType="tv"
              title={show?.title || show?.name || 'TV Show'}
            />
          </div>
        </div>
      )}

      {/* Add to Collection Modal */}
      <AddToCollectionModal
        isOpen={showAddToCollection}
        mediaId={parseInt(id!)}
        mediaType="tv"
        onClose={() => setShowAddToCollection(false)}
      />
    </Layout>
  )
}
