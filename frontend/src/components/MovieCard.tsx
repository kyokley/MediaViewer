import { useNavigate } from 'react-router-dom'
import { Movie } from '../types/api'

interface MovieCardProps {
  movie: Movie
}

export default function MovieCard({ movie }: MovieCardProps) {
  const navigate = useNavigate()

  return (
    <div
      onClick={() => navigate(`/movies/${movie.id}`)}
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
        {movie.poster_image_url ? (
          <img
            src={movie.poster_image_url}
            alt={movie.title || movie.name}
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
          {movie.title || movie.name}
        </h3>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
          {movie.release_date ? new Date(movie.release_date).getFullYear() : 'N/A'}
        </p>

        {/* Genres */}
        {movie.genres && movie.genres.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {movie.genres.slice(0, 2).map((genre) => (
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
        {movie.description && (
          <p className="text-xs mt-3 line-clamp-2" style={{ color: 'var(--text-tertiary)' }}>
            {movie.description}
          </p>
        )}
      </div>
    </div>
  )
}
