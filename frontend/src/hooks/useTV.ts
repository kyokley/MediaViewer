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

interface MediaWaiterMetadata {
  video_file: string
  subtitle_files: string[]
  title: string
  filename: string
  hashPath: string
  next_link: string | null
  previous_link: string | null
  files: Array<{
    path: string
    hashedWaiterPath: string
    subtitleFiles: Array<{ waiter_path: string }>
  }>
}

export function useEpisodeStream(episodeId: number | null) {
  const [streamUrl, setStreamUrl] = useState<string | null>(null)
  const [metadata, setMetadata] = useState<MediaWaiterMetadata | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!episodeId) {
      setStreamUrl(null)
      setMetadata(null)
      return
    }

    const fetchStreamUrl = async () => {
      setIsLoading(true)
      setError(null)

      try {
        // Step 1: Get the stream URL with GUID from MediaViewer API
        const response = await apiClient.get<{
          stream_url: string
          episode_id: number
          episode_name: string
          guid: string
        }>(`/episodes/${episodeId}/stream/`)

        // Ensure the URL has http:// prefix
        let baseUrl = response.data.stream_url
        if (!baseUrl.startsWith('http://') && !baseUrl.startsWith('https://')) {
          baseUrl = `http://${baseUrl}`
        }

        // Step 2: Fetch JSON metadata from MediaWaiter autoplay endpoint
        // The stream_url is like: http://localhost:5000/waiter/file/{guid}/
        // We need to append 'autoplay/json' to get the video player metadata
        const jsonUrl = `${baseUrl}${baseUrl.endsWith('/') ? '' : '/'}autoplay/json`

        const metadataResponse = await fetch(jsonUrl)
        if (!metadataResponse.ok) {
          throw new Error('Failed to fetch video metadata from MediaWaiter')
        }

        const metadataJson: MediaWaiterMetadata = await metadataResponse.json()

        // Extract the direct video URL from metadata
        const directVideoUrl = metadataJson.video_file

        setStreamUrl(directVideoUrl)
        setMetadata(metadataJson)
      } catch (err: any) {
        setError(
          err.response?.data?.error?.message ||
          err.message ||
            'Failed to fetch stream URL'
        )
      } finally {
        setIsLoading(false)
      }
    }

    fetchStreamUrl()
  }, [episodeId])

  return { streamUrl, metadata, isLoading, error }
}
