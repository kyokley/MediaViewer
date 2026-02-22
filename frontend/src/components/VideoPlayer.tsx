import { useEffect, useRef, useState } from 'react'
import { apiClient } from '../utils/api'
import { useEpisodeStream } from '../hooks/useTV'

interface VideoPlayerProps {
  mediaId: number
  mediaType: 'movie' | 'tv'
  title: string
  onProgressUpdate?: (currentTime: number, duration: number) => void
}

export default function VideoPlayer({
  mediaId,
  mediaType,
  title,
  onProgressUpdate,
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [volume, setVolume] = useState(1)
  const [fullscreen, setFullscreen] = useState(false)

  // Fetch stream URL for episodes
  const { streamUrl, metadata, isLoading: isLoadingStream, error: streamError } = useEpisodeStream(
    mediaType === 'tv' ? mediaId : null
  )

  // Set error if stream fetch fails
  useEffect(() => {
    if (streamError) {
      setError(streamError)
      setIsLoading(false)
    }
  }, [streamError])

  // Fetch video progress on mount
  useEffect(() => {
    const fetchVideoProgress = async () => {
      try {
        const response = await apiClient.get('/video-progress/')
        const progress = response.data.data.find(
          (p: any) => p.media_id === mediaId && p.media_type === mediaType
        )
        if (progress && videoRef.current) {
          videoRef.current.currentTime = progress.current_time_seconds || 0
          setCurrentTime(progress.current_time_seconds || 0)
        }
      } catch (err) {
        console.log('No saved progress found')
      }
    }

    fetchVideoProgress()
  }, [mediaId, mediaType])

  // Save progress periodically
  useEffect(() => {
    if (!videoRef.current || !isPlaying) return

    const interval = setInterval(async () => {
      const current = videoRef.current?.currentTime || 0
      try {
        await apiClient.post('/video-progress/', {
          media_id: mediaId,
          media_type: mediaType,
          current_time_seconds: Math.floor(current),
        })
      } catch (err) {
        console.log('Could not save progress')
      }
    }, 5000) // Save every 5 seconds

    return () => clearInterval(interval)
  }, [mediaId, mediaType, isPlaying])

  const handlePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause()
      } else {
        videoRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime)
      onProgressUpdate?.(videoRef.current.currentTime, duration)
    }
  }

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration)
      setIsLoading(false)
    }
  }

  const handleFullscreen = () => {
    const container = document.getElementById('video-player-container')
    if (container) {
      if (!document.fullscreenElement) {
        container.requestFullscreen()
        setFullscreen(true)
      } else {
        document.exitFullscreen()
        setFullscreen(false)
      }
    }
  }

  const formatTime = (seconds: number): string => {
    if (!seconds || isNaN(seconds)) return '0:00'
    const minutes = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }

  // Determine which video URL to use
  const videoUrl = streamUrl || null

  return (
    <div
      id="video-player-container"
      className={`relative bg-black rounded-lg overflow-hidden ${fullscreen ? 'fixed inset-0 z-50' : ''}`}
    >
      <div className="relative pt-[56.25%]">
        <div className="absolute inset-0 flex items-center justify-center bg-black">
          <>
            <video
              ref={videoRef}
              className="absolute inset-0 w-full h-full"
              onTimeUpdate={handleTimeUpdate}
              onLoadedMetadata={handleLoadedMetadata}
              onError={(e) => {
                console.error('Video load error:', e)
                setError('Failed to load video. Please check the stream URL or try again.')
                setIsLoading(false)
              }}
              src={videoUrl || undefined}
              crossOrigin="anonymous"
            >
              {/* Add subtitle tracks from metadata */}
              {metadata?.subtitle_files?.map((subtitleUrl, index) => (
                <track
                  key={index}
                  kind="subtitles"
                  src={subtitleUrl}
                  label={`Subtitles ${index + 1}`}
                  default={index === 0}
                />
              ))}
            </video>

            {error && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/80 z-10">
                <div className="text-white text-center p-4 max-w-md">
                  <p className="text-red-500 mb-2 text-lg">Video Player Error</p>
                  <p className="text-gray-300 text-sm mb-4">{error}</p>
                </div>
              </div>
            )}

            {!error && (
              <>
                {/* Video Controls Overlay */}
                <div className="absolute inset-0 flex flex-col justify-between opacity-0 hover:opacity-100 transition-opacity duration-300 bg-gradient-to-t from-black/80 via-transparent to-black/20">
                  {/* Top Bar */}
                  <div className="p-4 flex justify-between items-center">
                    <h3 className="text-white font-semibold">{title}</h3>
                    {fullscreen && (
                      <button
                        onClick={handleFullscreen}
                        className="text-white hover:text-gray-300 transition"
                        title="Exit fullscreen"
                      >
                        ✕
                      </button>
                    )}
                  </div>

                  {/* Center Play Button */}
                  <div className="flex justify-center items-center">
                    <button
                      onClick={handlePlayPause}
                      className="w-16 h-16 rounded-full bg-white/30 hover:bg-white/50 transition flex items-center justify-center text-white text-4xl"
                    >
                      {isPlaying ? '⏸' : '▶'}
                    </button>
                  </div>

                  {/* Bottom Controls */}
                  <div className="p-4 space-y-2">
                    {/* Progress Bar */}
                    <input
                      type="range"
                      min="0"
                      max={duration || 0}
                      value={currentTime}
                      onChange={(e) => {
                        const newTime = parseFloat(e.target.value)
                        if (videoRef.current) {
                          videoRef.current.currentTime = newTime
                          setCurrentTime(newTime)
                        }
                      }}
                      className="w-full h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer accent-blue-500"
                    />

                    {/* Control Bar */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <button
                          onClick={handlePlayPause}
                          className="text-white hover:text-gray-300 transition"
                        >
                          {isPlaying ? '⏸' : '▶'}
                        </button>

                        {/* Volume Control */}
                        <div className="flex items-center gap-2 group">
                          <button className="text-white hover:text-gray-300 transition">
                            {volume === 0 ? '🔇' : '🔊'}
                          </button>
                          <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.1"
                            value={volume}
                            onChange={(e) => {
                              const newVolume = parseFloat(e.target.value)
                              setVolume(newVolume)
                              if (videoRef.current) {
                                videoRef.current.volume = newVolume
                              }
                            }}
                            className="w-0 group-hover:w-24 transition-all duration-300 h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer accent-blue-500"
                          />
                        </div>

                        {/* Time Display */}
                        <span className="text-white text-sm">
                          {formatTime(currentTime)} / {formatTime(duration)}
                        </span>
                      </div>

                      {/* Fullscreen Button */}
                      <button
                        onClick={handleFullscreen}
                        className="text-white hover:text-gray-300 transition"
                        title="Toggle fullscreen"
                      >
                        ⛶
                      </button>
                    </div>
                  </div>
                </div>

                {/* Loading Indicator */}
                {isLoading && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-8 h-8 border-4 border-gray-600 border-t-white rounded-full animate-spin"></div>
                  </div>
                )}
              </>
            )}
          </>
        </div>
      </div>

      {/* Loading or No Stream Notice */}
      {!streamUrl && !error && isLoadingStream && (
        <div className="mt-2 text-center">
          <div className="inline-block bg-blue-500/10 border border-blue-500/30 rounded-lg px-4 py-2">
            <p className="text-blue-500 text-xs font-medium">
              🔄 Loading video stream...
            </p>
          </div>
        </div>
      )}

      {!streamUrl && !error && !isLoadingStream && (
        <div className="mt-2 text-center">
          <div className="inline-block bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-2">
            <p className="text-red-500 text-xs font-medium">
              ⚠️ No stream URL available
            </p>
            <p className="text-red-600 text-xs mt-1">
              Requested: {title}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
