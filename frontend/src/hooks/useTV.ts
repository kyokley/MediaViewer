import { useState, useEffect } from 'react'
import { TVShow, ApiResponse, EpisodesResponse } from '../types/api'
import { apiClient } from '../utils/api'

export function useTV(
  page = 1,
  limit = 20,
  search = '',
  genreId?: number,
  sortBy = 'date_added'
) {
  const [shows, setShows] = useState<TVShow[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    const fetchShows = async () => {
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

        const response = await apiClient.get<ApiResponse<TVShow[]>>(
          '/tv/',
          { params }
        )

        setShows(response.data.data)
        setTotal(response.data.pagination?.total || 0)
      } catch (err: any) {
        setError(
          err.response?.data?.error?.message ||
            'Failed to fetch TV shows'
        )
      } finally {
        setIsLoading(false)
      }
    }

    fetchShows()
  }, [page, limit, search, genreId, sortBy])

  return { shows, isLoading, error, total }
}

export function useEpisodes(tvId: number) {
  const [seasons, setSeasons] = useState<EpisodesResponse['data']>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [totalEpisodes, setTotalEpisodes] = useState(0)
  const [totalSeasons, setTotalSeasons] = useState(0)

  useEffect(() => {
    const fetchEpisodes = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const response = await apiClient.get<EpisodesResponse>(
          `/tv/${tvId}/episodes/`
        )

        setSeasons(response.data.data)
        setTotalEpisodes(response.data.total_episodes)
        setTotalSeasons(response.data.total_seasons)
      } catch (err: any) {
        setError(
          err.response?.data?.error?.message ||
            'Failed to fetch episodes'
        )
      } finally {
        setIsLoading(false)
      }
    }

    if (tvId) {
      fetchEpisodes()
    }
  }, [tvId])

  return { seasons, isLoading, error, totalEpisodes, totalSeasons }
}
