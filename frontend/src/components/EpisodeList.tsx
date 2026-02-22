import { useState } from 'react'
import { Season, Episode } from '../types/api'
import './EpisodeList.css'

interface EpisodeListProps {
  seasons: Season[]
  isLoading: boolean
  error: string | null
}

export function EpisodeList({ seasons, isLoading, error }: EpisodeListProps) {
  const [expandedSeasons, setExpandedSeasons] = useState<Set<number>>(
    new Set([1]) // First season expanded by default
  )

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

  if (isLoading) {
    return <div className="episode-list-loading">Loading episodes...</div>
  }

  if (error) {
    return <div className="episode-list-error">Error: {error}</div>
  }

  if (!seasons || seasons.length === 0) {
    return <div className="episode-list-empty">No episodes found</div>
  }

  return (
    <div className="episode-list">
      <h2>Episodes</h2>
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
                <div
                  key={episode.id}
                  className={`episode-card ${episode.watched ? 'watched' : ''}`}
                >
                  <div className="episode-number">
                    E{episode.episode.toString().padStart(2, '0')}
                  </div>
                  <div className="episode-info">
                    <div className="episode-name">
                      {episode.episode_name || episode.display_name}
                    </div>
                    <div className="episode-date">
                      {new Date(episode.date_created).toLocaleDateString()}
                    </div>
                  </div>
                  {episode.watched && (
                    <div className="episode-watched-badge">✓</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
