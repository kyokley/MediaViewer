import { useState, useEffect } from 'react'
import { Movie, ApiResponse, Genre } from '../types/api'
import { apiClient } from '../utils/api'

export function useMovies(
  page = 1,
  limit = 20,
  search = '',
  genreId?: number,
  sortBy = 'date_added'
) {
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
          sort_by: sortBy,
        }

        if (search) {
          params.search = search
        }

        if (genreId) {
          params.genre = genreId
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
  }, [page, limit, search, genreId, sortBy])

  return { movies, isLoading, error, total }
}

export function useGenres() {
  const [genres, setGenres] = useState<Genre[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchGenres = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const response = await apiClient.get<ApiResponse<Genre[]>>('/genres/')
        setGenres(response.data.data)
      } catch (err: any) {
        setError(
          err.response?.data?.error?.message ||
            'Failed to fetch genres'
        )
      } finally {
        setIsLoading(false)
      }
    }

    fetchGenres()
  }, [])

  return { genres, isLoading, error }
}
