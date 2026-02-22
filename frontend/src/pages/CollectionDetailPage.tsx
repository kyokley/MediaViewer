import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import MovieCard from '../components/MovieCard'
import TVCard from '../components/TVCard'
import { useCollectionItems } from '../hooks/useCollections'

export default function CollectionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const collectionId = parseInt(id || '0')
  const { items, collection, isLoading, error, removeItem } = useCollectionItems(collectionId)
  const [removingId, setRemovingId] = useState<number | null>(null)
  const [removeError, setRemoveError] = useState<string | null>(null)

  const handleRemoveItem = async (itemId: number, mediaType: 'movie' | 'tv') => {
    setRemovingId(itemId)
    setRemoveError(null)

    try {
      await removeItem(itemId, mediaType)
    } catch (err: any) {
      setRemoveError(err)
    } finally {
      setRemovingId(null)
    }
  }

  if (isLoading) {
    return (
      <Layout>
        <LoadingSpinner />
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout>
        <div className="space-y-4">
          <button
            onClick={() => navigate('/collections')}
            className="text-blue-400 hover:text-blue-300 transition"
          >
            ← Back to Collections
          </button>
          <ErrorAlert message={error} />
        </div>
      </Layout>
    )
  }

  if (!collection) {
    return (
      <Layout>
        <div className="text-center py-12 text-gray-400">
          Collection not found
        </div>
      </Layout>
    )
  }

  const movies = items.filter((item) => item.media_type === 'movie')
  const tvShows = items.filter((item) => item.media_type === 'tv')

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <button
            onClick={() => navigate('/collections')}
            className="text-blue-400 hover:text-blue-300 transition mb-4"
          >
            ← Back to Collections
          </button>
          <h1 className="text-4xl font-bold text-white mb-2">{collection.name}</h1>
          <p className="text-gray-400">
            {collection.item_count} {collection.item_count === 1 ? 'item' : 'items'}
          </p>
        </div>

        {removeError && <ErrorAlert message={removeError} />}

        {/* Empty State */}
        {items.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            This collection is empty. Add movies or TV shows from their detail pages!
          </div>
        ) : (
          <>
            {/* Movies Section */}
            {movies.length > 0 && (
              <div>
                <h2 className="text-2xl font-semibold text-white mb-4">
                  Movies ({movies.length})
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                  {movies.map((movie) => (
                    <div key={movie.id} className="relative group">
                      <MovieCard movie={movie} />
                      <button
                        onClick={() => handleRemoveItem(movie.id, 'movie')}
                        disabled={removingId === movie.id}
                        className="absolute top-2 right-2 bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-lg text-sm opacity-0 group-hover:opacity-100 transition disabled:opacity-50"
                      >
                        {removingId === movie.id ? 'Removing...' : 'Remove'}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TV Shows Section */}
            {tvShows.length > 0 && (
              <div>
                <h2 className="text-2xl font-semibold text-white mb-4">
                  TV Shows ({tvShows.length})
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                  {tvShows.map((show) => (
                    <div key={show.id} className="relative group">
                      <TVCard show={show} />
                      <button
                        onClick={() => handleRemoveItem(show.id, 'tv')}
                        disabled={removingId === show.id}
                        className="absolute top-2 right-2 bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-lg text-sm opacity-0 group-hover:opacity-100 transition disabled:opacity-50"
                      >
                        {removingId === show.id ? 'Removing...' : 'Remove'}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  )
}
