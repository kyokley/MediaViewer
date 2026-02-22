import { Episode } from '../types/api'
import './EpisodeDetailModal.css'

interface EpisodeDetailModalProps {
  episode: Episode | null
  showName: string
  onClose: () => void
  onPlayEpisode?: (episode: Episode) => void
}

export function EpisodeDetailModal({
  episode,
  showName,
  onClose,
  onPlayEpisode,
}: EpisodeDetailModalProps) {
  if (!episode) return null

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
        month: 'long',
        day: 'numeric',
      })
    } catch {
      return 'Unknown'
    }
  }

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  return (
    <div className="episode-modal-backdrop" onClick={handleBackdropClick}>
      <div className="episode-modal">
        {/* Close Button */}
        <button className="episode-modal-close" onClick={onClose}>
          ✕
        </button>

        {/* Episode Thumbnail */}
        {episode.thumbnail_url && (
          <div className="episode-modal-thumbnail">
            <img src={episode.thumbnail_url} alt={episode.episode_name} />
            {episode.watched && (
              <div className="watched-badge-modal">
                <span>✓ Watched</span>
              </div>
            )}
          </div>
        )}

        {/* Episode Details */}
        <div className="episode-modal-content">
          <div className="episode-modal-header">
            <div className="episode-modal-show">{showName}</div>
            <h2 className="episode-modal-title">
              S{episode.season.toString().padStart(2, '0')} E
              {episode.episode.toString().padStart(2, '0')}:{' '}
              {episode.episode_name || 'Untitled'}
            </h2>
          </div>

          {/* Metadata */}
          <div className="episode-modal-metadata">
            {episode.air_date && (
              <div className="metadata-row">
                <span className="metadata-label">Air Date</span>
                <span className="metadata-value">{formatDate(episode.air_date)}</span>
              </div>
            )}
            <div className="metadata-row">
              <span className="metadata-label">Added</span>
              <span className="metadata-value">
                {formatDate(episode.date_created)}
              </span>
            </div>
            {episode.file_size && (
              <div className="metadata-row">
                <span className="metadata-label">File Size</span>
                <span className="metadata-value">
                  {formatFileSize(episode.file_size)}
                </span>
              </div>
            )}
          </div>

          {/* Description */}
          {(episode.overview || episode.plot) && (
            <div className="episode-modal-description">
              <h3>Overview</h3>
              <p>{episode.overview || episode.plot}</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="episode-modal-actions">
            <button
              className="btn-primary"
              onClick={() => onPlayEpisode?.(episode)}
            >
              <svg className="btn-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Play Episode
            </button>
            <button className="btn-secondary" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
