import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import { useCollections } from '../hooks/useCollections'

export default function CollectionsPage() {
  const navigate = useNavigate()
  const { collections, isLoading, error, createCollection, deleteCollection } =
    useCollections()
  const [newCollectionName, setNewCollectionName] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null)

  const handleCreateCollection = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newCollectionName.trim()) return

    setIsCreating(true)
    setCreateError(null)

    try {
      await createCollection(newCollectionName)
      setNewCollectionName('')
    } catch (err: any) {
      setCreateError(err)
    } finally {
      setIsCreating(false)
    }
  }

  const handleDeleteCollection = async (id: number) => {
    setDeletingId(id)
    setDeleteError(null)

    try {
      await deleteCollection(id)
      setConfirmDelete(null)
    } catch (err: any) {
      setDeleteError(err)
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold text-white mb-6">Collections</h1>

          {/* Create Collection Form */}
          <form onSubmit={handleCreateCollection} className="flex gap-2 mb-8">
            <input
              type="text"
              placeholder="New collection name..."
              value={newCollectionName}
              onChange={(e) => setNewCollectionName(e.target.value)}
              className="flex-1 px-4 py-3 bg-gray-800 text-white rounded-lg border border-gray-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 outline-none transition"
            />
            <button
              type="submit"
              disabled={isCreating || !newCollectionName.trim()}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg font-medium transition"
            >
              {isCreating ? 'Creating...' : 'Create'}
            </button>
          </form>

          {createError && <ErrorAlert message={createError} />}
        </div>

        {/* Error Message */}
        {error && <ErrorAlert message={error} />}

        {/* Collections List */}
        {isLoading ? (
          <LoadingSpinner />
        ) : collections.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            No collections yet. Create your first collection!
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {collections.map((collection) => (
              <div
                key={collection.id}
                className="bg-gray-800 rounded-lg p-6 hover:shadow-lg hover:shadow-blue-500/50 transition"
              >
                <h3 className="text-xl font-semibold text-white mb-2">
                  {collection.name}
                </h3>
                <p className="text-gray-400 mb-4">
                  {collection.item_count} items
                </p>

                {deleteError && confirmDelete === collection.id && (
                  <ErrorAlert message={deleteError} />
                )}

                {confirmDelete === collection.id ? (
                  <div className="space-y-2">
                    <p className="text-sm text-gray-300 mb-3">
                      Are you sure you want to delete this collection?
                    </p>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleDeleteCollection(collection.id)}
                        disabled={deletingId === collection.id}
                        className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white rounded-lg transition text-sm font-medium"
                      >
                        {deletingId === collection.id ? 'Deleting...' : 'Confirm'}
                      </button>
                      <button
                        onClick={() => setConfirmDelete(null)}
                        disabled={deletingId === collection.id}
                        className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-600 text-white rounded-lg transition text-sm font-medium"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex gap-2">
                    <button
                      onClick={() => navigate(`/collections/${collection.id}`)}
                      className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm font-medium"
                    >
                      View
                    </button>
                    <button
                      onClick={() => setConfirmDelete(collection.id)}
                      className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition text-sm font-medium"
                    >
                      Delete
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  )
}
