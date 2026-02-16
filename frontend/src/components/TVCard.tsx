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
      className="bg-gray-800 rounded-lg overflow-hidden hover:shadow-lg hover:shadow-blue-500/50 transition transform hover:scale-105 cursor-pointer"
    >
      {/* Poster Image */}
      <div className="relative h-48 bg-gray-700 overflow-hidden">
        {show.poster_image_url ? (
          <img
            src={show.poster_image_url}
            alt={show.title || show.name}
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
        <h3 className="font-semibold text-white truncate">{show.title || show.name}</h3>
        <p className="text-sm text-gray-400 mt-1">
          {show.first_air_date ? new Date(show.first_air_date).getFullYear() : 'N/A'}
        </p>

        {/* Genres */}
        {show.genres && show.genres.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {show.genres.slice(0, 2).map((genre: any) => (
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
        {show.description && (
          <p className="text-xs text-gray-400 mt-3 line-clamp-2">
            {show.description}
          </p>
        )}
      </div>
    </div>
  )
}
