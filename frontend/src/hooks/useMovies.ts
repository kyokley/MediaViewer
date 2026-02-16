import { useState, useEffect } from 'react'
import { Movie, ApiResponse } from '../types/api'
import { apiClient } from '../utils/api'

export function useMovies(page = 1, limit = 20, search = '') {
  const [movies, setMovies] = useState<Movie[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    const fetchMovies = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const offset = (page - 1) * limit
        const params: any = {
          limit,
          offset,
        }

        if (search) {
          params.search = search
        }

        const response = await apiClient.get<ApiResponse<Movie[]>>(
          '/movies/',
          { params }
        )

        setMovies(response.data.data)
        setTotal(response.data.pagination?.total || 0)
      } catch (err: any) {
        setError(
          err.response?.data?.error?.message ||
            'Failed to fetch movies'
        )
      } finally {
        setIsLoading(false)
      }
    }

    fetchMovies()
  }, [page, limit, search])

  return { movies, isLoading, error, total }
}
