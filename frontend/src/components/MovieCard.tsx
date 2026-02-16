import { Movie } from '../types/api'

interface MovieCardProps {
  movie: Movie
}

export default function MovieCard({ movie }: MovieCardProps) {
  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden hover:shadow-lg hover:shadow-blue-500/50 transition transform hover:scale-105">
      {/* Poster Image */}
      <div className="relative h-48 bg-gray-700 overflow-hidden">
        {movie.poster_image_url ? (
          <img
            src={movie.poster_image_url}
            alt={movie.title || movie.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-500">
            No poster
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 className="font-semibold text-white truncate">{movie.title || movie.name}</h3>
        <p className="text-sm text-gray-400 mt-1">
          {movie.release_date ? new Date(movie.release_date).getFullYear() : 'N/A'}
        </p>

        {/* Genres */}
        {movie.genres && movie.genres.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {movie.genres.slice(0, 2).map((genre) => (
              <span
                key={genre.id}
                className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded"
              >
                {genre.name}
              </span>
            ))}
          </div>
        )}

        {/* Description Preview */}
        {movie.description && (
          <p className="text-xs text-gray-400 mt-3 line-clamp-2">
            {movie.description}
          </p>
        )}
      </div>
    </div>
  )
}
