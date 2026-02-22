import { useState } from 'react'
import { Season, Episode } from '../types/api'
import { EpisodeCard } from './EpisodeCard'
import { EpisodeDetailModal } from './EpisodeDetailModal'
import './EpisodeList.css'

interface EpisodeListProps {
  seasons: Season[]
  isLoading: boolean
  error: string | null
  showName?: string
  onPlayEpisode?: (episode: Episode) => void
}

export function EpisodeList({
  seasons,
  isLoading,
  error,
  showName = 'TV Show',
  onPlayEpisode,
}: EpisodeListProps) {
  const [expandedSeasons, setExpandedSeasons] = useState<Set<number>>(
    new Set([1]) // First season expanded by default
  )
  const [selectedEpisode, setSelectedEpisode] = useState<Episode | null>(null)

  const toggleSeason = (seasonNumber: number) => {
    setExpandedSeasons((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(seasonNumber)) {
        newSet.delete(seasonNumber)
      } else {
        newSet.add(seasonNumber)
      }
      return newSet
    })
  }

  const handleEpisodeClick = (episode: Episode) => {
    setSelectedEpisode(episode)
  }

  const handleCloseModal = () => {
    setSelectedEpisode(null)
  }

  if (isLoading) {
    return <div className="episode-list-loading">Loading episodes...</div>
  }

  if (error) {
    return <div className="episode-list-error">Error: {error}</div>
  }

  if (!seasons || seasons.length === 0) {
    return <div className="episode-list-empty">No episodes found</div>
  }

  // Calculate total episode count
  const totalEpisodes = seasons.reduce(
    (sum, season) => sum + season.episodes.length,
    0
  )

  return (
    <>
      <div className="episode-list">
        <div className="episode-list-header">
          <h2>Episodes</h2>
          <span className="episode-count-badge">
            {totalEpisodes} episode{totalEpisodes !== 1 ? 's' : ''} across{' '}
            {seasons.length} season{seasons.length !== 1 ? 's' : ''}
          </span>
        </div>

        {seasons.map((season) => (
          <div key={season.season_number} className="season-container">
            <button
              className="season-header"
              onClick={() => toggleSeason(season.season_number)}
            >
              <span className="season-title">
                Season {season.season_number}
                <span className="episode-count">
                  {' '}
                  ({season.episodes.length} episode
                  {season.episodes.length !== 1 ? 's' : ''})
                </span>
              </span>
              <span
                className={`season-toggle ${
                  expandedSeasons.has(season.season_number) ? 'expanded' : ''
                }`}
              >
                ▼
              </span>
            </button>

            {expandedSeasons.has(season.season_number) && (
              <div className="episodes-container">
                {season.episodes.map((episode: Episode) => (
                  <EpisodeCard
                    key={episode.id}
                    episode={episode}
                    onEpisodeClick={handleEpisodeClick}
                  />
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Episode Detail Modal */}
      <EpisodeDetailModal
        episode={selectedEpisode}
        showName={showName}
        onClose={handleCloseModal}
        onPlayEpisode={onPlayEpisode}
      />
    </>
  )
}
