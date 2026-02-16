import { useState } from 'react'
import { Movie, TVShow, ApiResponse } from '../types/api'
import { apiClient } from '../utils/api'

export interface SearchResult {
  movies: Movie[]
  tv: TVShow[]
}

export function useSearch() {
  const [results, setResults] = useState<SearchResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = async (query: string, type: 'all' | 'movie' | 'tv' = 'all', limit = 50) => {
    if (!query.trim()) {
      setResults(null)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const params: any = {
        query,
        limit,
      }

      if (type !== 'all') {
        params.type = type
      }

      const response = await apiClient.get<
        ApiResponse<{ movies?: Movie[]; tv?: TVShow[] }>
      >('/search/', { params })

      const data = response.data.data
      setResults({
        movies: data.movies || [],
        tv: data.tv || [],
      })
    } catch (err: any) {
      setError(
        err.response?.data?.error?.message ||
          'Failed to search'
      )
      setResults(null)
    } finally {
      setIsLoading(false)
    }
  }

  return { search, results, isLoading, error }
}
