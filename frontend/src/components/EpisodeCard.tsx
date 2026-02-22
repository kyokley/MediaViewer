import { Episode } from '../types/api'
import './EpisodeCard.css'

interface EpisodeCardProps {
  episode: Episode
  onEpisodeClick?: (episode: Episode) => void
}

export function EpisodeCard({ episode, onEpisodeClick }: EpisodeCardProps) {
  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown'
    const gb = bytes / (1024 * 1024 * 1024)
    return `${gb.toFixed(2)} GB`
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown'
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    } catch {
      return 'Unknown'
    }
  }

  return (
    <div
      className={`episode-card-enhanced ${episode.watched ? 'watched' : ''}`}
      onClick={() => onEpisodeClick?.(episode)}
    >
      {/* Episode Thumbnail */}
      <div className="episode-thumbnail">
        {episode.thumbnail_url ? (
          <img src={episode.thumbnail_url} alt={episode.episode_name} />
        ) : (
          <div className="episode-thumbnail-placeholder">
            <span className="episode-number-large">
              {episode.episode.toString().padStart(2, '0')}
            </span>
          </div>
        )}
        {episode.watched && (
          <div className="watched-overlay">
            <div className="watched-badge">✓</div>
          </div>
        )}
      </div>

      {/* Episode Info */}
      <div className="episode-info-enhanced">
        <div className="episode-header">
          <span className="episode-number-label">
            Episode {episode.episode}
          </span>
          {episode.air_date && (
            <span className="episode-air-date">{formatDate(episode.air_date)}</span>
          )}
        </div>

        <h4 className="episode-title">
          {episode.episode_name || episode.display_name}
        </h4>

        {episode.plot && (
          <p className="episode-plot">{episode.plot}</p>
        )}

        <div className="episode-metadata">
          {episode.file_size && (
            <span className="metadata-item">
              <svg className="metadata-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              {formatFileSize(episode.file_size)}
            </span>
          )}
          <span className="metadata-item">
            <svg className="metadata-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Added {formatDate(episode.date_created)}
          </span>
        </div>
      </div>
    </div>
  )
}
