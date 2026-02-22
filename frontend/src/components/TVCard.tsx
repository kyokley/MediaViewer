import { useNavigate } from 'react-router-dom'
import { TVShow } from '../types/api'

interface TVCardProps {
  show: TVShow
}

export default function TVCard({ show }: TVCardProps) {
  const navigate = useNavigate()

  return (
    <div
      onClick={() => navigate(`/tv/${show.id}`)}
      className="rounded-lg overflow-hidden transition transform hover:scale-105 cursor-pointer"
      style={{
        backgroundColor: 'var(--bg-secondary)',
        boxShadow: 'var(--shadow-md)',
      }}
    >
      {/* Poster Image */}
      <div
        className="relative h-48 overflow-hidden"
        style={{ backgroundColor: 'var(--bg-tertiary)' }}
      >
        {show.poster_image_url ? (
          <img
            src={show.poster_image_url}
            alt={show.title || show.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div
            className="w-full h-full flex items-center justify-center"
            style={{ color: 'var(--text-tertiary)' }}
          >
            No poster
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 className="font-semibold truncate" style={{ color: 'var(--text-primary)' }}>
          {show.title || show.name}
        </h3>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
          {show.first_air_date ? new Date(show.first_air_date).getFullYear() : 'N/A'}
        </p>

        {/* Genres */}
        {show.genres && show.genres.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {show.genres.slice(0, 2).map((genre: any) => (
              <span
                key={genre.id}
                className="text-xs px-2 py-1 rounded"
                style={{
                  backgroundColor: 'var(--bg-tertiary)',
                  color: 'var(--text-secondary)',
                }}
              >
                {genre.name}
              </span>
            ))}
          </div>
        )}

        {/* Description Preview */}
        {show.description && (
          <p className="text-xs mt-3 line-clamp-2" style={{ color: 'var(--text-tertiary)' }}>
            {show.description}
          </p>
        )}
      </div>
    </div>
  )
}
