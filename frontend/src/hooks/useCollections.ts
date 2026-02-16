import { useState, useEffect } from 'react'
import { Collection, ApiResponse } from '../types/api'
import { apiClient } from '../utils/api'

export function useCollections(page = 1, limit = 20) {
  const [collections, setCollections] = useState<Collection[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    const fetchCollections = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const offset = (page - 1) * limit
        const response = await apiClient.get<ApiResponse<Collection[]>>(
          '/collections/',
          { params: { limit, offset } }
        )

        setCollections(response.data.data)
        setTotal(response.data.pagination?.total || 0)
      } catch (err: any) {
        setError(
          err.response?.data?.error?.message ||
            'Failed to fetch collections'
        )
      } finally {
        setIsLoading(false)
      }
    }

    fetchCollections()
  }, [page, limit])

  const createCollection = async (name: string) => {
    try {
      const response = await apiClient.post('/collections/', { name })
      setCollections([...collections, response.data.data])
      return response.data.data
    } catch (err: any) {
      throw err.response?.data?.error?.message || 'Failed to create collection'
    }
  }

  const deleteCollection = async (id: number) => {
    try {
      await apiClient.delete(`/collections/${id}/`)
      setCollections(collections.filter((c) => c.id !== id))
    } catch (err: any) {
      throw err.response?.data?.error?.message || 'Failed to delete collection'
    }
  }

  return { collections, isLoading, error, total, createCollection, deleteCollection }
}
