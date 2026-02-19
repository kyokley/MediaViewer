import { useEffect, useRef, useState } from 'react'
import { apiClient } from '../utils/api'

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

  // For demo purposes, use a placeholder video or show a message
  const demoVideoUrl =
    'https://commondatastorage.googleapis.com/gtv-videos-library/sample/BigBuckBunny.mp4'

  return (
    <div
      id="video-player-container"
      className={`relative bg-black rounded-lg overflow-hidden ${fullscreen ? 'fixed inset-0 z-50' : ''}`}
    >
      <div className="relative pt-[56.25%]">
        <div className="absolute inset-0 flex items-center justify-center bg-black">
          {error ? (
            <div className="text-white text-center p-4">
              <p className="text-red-500 mb-2">Video Player Error</p>
              <p className="text-gray-300 text-sm">{error}</p>
              <p className="text-gray-400 text-xs mt-4">
                Video streaming is not available for this content in development mode.
              </p>
            </div>
          ) : (
            <>
              <video
                ref={videoRef}
                className="absolute inset-0 w-full h-full"
                onTimeUpdate={handleTimeUpdate}
                onLoadedMetadata={handleLoadedMetadata}
                onError={() => {
                  setError('Failed to load video')
                  setIsLoading(false)
                }}
                src={demoVideoUrl}
              />

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
        </div>
      </div>

      {/* Demo Notice */}
      {!error && (
        <div className="absolute -bottom-8 left-0 right-0 text-center text-gray-500 text-xs">
          <p>Playing demo video (Big Buck Bunny) - replace with actual video stream</p>
        </div>
      )}
    </div>
  )
}
