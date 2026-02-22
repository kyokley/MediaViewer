import { useState } from 'react'
import { useCollections } from '../hooks/useCollections'
import { apiClient } from '../utils/api'
import LoadingSpinner from './LoadingSpinner'
import ErrorAlert from './ErrorAlert'

interface AddToCollectionModalProps {
  isOpen: boolean
  mediaId: number
  mediaType: 'movie' | 'tv'
  onClose: () => void
}

export default function AddToCollectionModal({
  isOpen,
  mediaId: _mediaId,
  mediaType: _mediaType,
  onClose,
}: AddToCollectionModalProps) {
  const { collections, isLoading } = useCollections()
  const [selectedCollectionId, setSelectedCollectionId] = useState<number | null>(null)
  const [isAdding, setIsAdding] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleAddToCollection = async () => {
    if (!selectedCollectionId) return

    setIsAdding(true)
    setError(null)
    setSuccess(false)

    try {
      // Add media to collection
      await apiClient.post(
        `/collections/${selectedCollectionId}/items/`,
        { media_id: _mediaId, media_type: _mediaType }
      )

      // Show success
      setSuccess(true)
      setTimeout(() => {
        onClose()
        setSelectedCollectionId(null)
        setSuccess(false)
      }, 1500)
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to add to collection')
    } finally {
      setIsAdding(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full">
        <h2 className="text-xl font-semibold text-white mb-4">Add to Collection</h2>

        {error && <ErrorAlert message={error} />}

        {success && (
          <div className="mb-4 p-3 bg-green-900/30 border border-green-600 text-green-400 rounded-lg">
            ✓ Added to collection successfully
          </div>
        )}

        {isLoading ? (
          <LoadingSpinner />
        ) : collections.length === 0 ? (
          <p className="text-gray-400 text-center py-4">
            No collections yet. Create one first!
          </p>
        ) : (
          <>
            <div className="space-y-2 mb-6">
              {collections.map((collection) => (
                <button
                  key={collection.id}
                  onClick={() => setSelectedCollectionId(collection.id)}
                  className={`w-full text-left px-4 py-3 rounded-lg transition ${
                    selectedCollectionId === collection.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  <span className="font-medium">{collection.name}</span>
                  <span className="text-xs opacity-75 ml-2">
                    ({collection.item_count} items)
                  </span>
                </button>
              ))}
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleAddToCollection}
                disabled={!selectedCollectionId || isAdding}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg transition font-medium"
              >
                {isAdding ? 'Adding...' : 'Add'}
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition font-medium"
              >
                Cancel
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
