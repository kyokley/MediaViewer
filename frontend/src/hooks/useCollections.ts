import { useState, useEffect } from 'react'
import { Collection, ApiResponse, Movie, TVShow } from '../types/api'
import { apiClient } from '../utils/api'

export interface CollectionItem extends Movie, TVShow {
  media_type: 'movie' | 'tv'
}

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

export function useCollectionItems(collectionId: number) {
  const [items, setItems] = useState<CollectionItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [collection, setCollection] = useState<Collection | null>(null)

  useEffect(() => {
    const fetchCollectionItems = async () => {
      setIsLoading(true)
      setError(null)

      try {
        // Fetch collection details
        const collectionResponse = await apiClient.get<Collection>(
          `/collections/${collectionId}/`
        )
        setCollection(collectionResponse.data)

        // Fetch collection items
        const itemsResponse = await apiClient.get<ApiResponse<CollectionItem[]>>(
          `/collections/${collectionId}/items/`
        )
        setItems(itemsResponse.data.data)
      } catch (err: any) {
        setError(
          err.response?.data?.error?.message ||
            'Failed to fetch collection items'
        )
      } finally {
        setIsLoading(false)
      }
    }

    if (collectionId) {
      fetchCollectionItems()
    }
  }, [collectionId])

  const removeItem = async (mediaId: number, mediaType: 'movie' | 'tv') => {
    try {
      await apiClient.delete(
        `/collections/${collectionId}/items/?media_id=${mediaId}&media_type=${mediaType}`
      )
      setItems(items.filter((item) => item.id !== mediaId || item.media_type !== mediaType))
    } catch (err: any) {
      throw err.response?.data?.error?.message || 'Failed to remove item from collection'
    }
  }

  return { items, collection, isLoading, error, removeItem }
}
