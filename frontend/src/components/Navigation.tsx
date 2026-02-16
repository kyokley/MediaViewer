import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../utils/authStore'

export default function Navigation() {
  const navigate = useNavigate()
  const logout = useAuthStore((state) => state.logout)
  const user = useAuthStore((state) => state.user)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav className="fixed top-0 w-full bg-gray-800 border-b border-gray-700 z-50">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="text-2xl font-bold text-blue-500">MV</div>
            <span className="text-lg font-semibold text-white">MediaViewer</span>
          </Link>

           {/* Navigation Links */}
           <div className="hidden md:flex items-center space-x-8">
             <Link
               to="/"
               className="text-gray-300 hover:text-white transition"
             >
               Home
             </Link>
             <Link
               to="/movies"
               className="text-gray-300 hover:text-white transition"
             >
               Movies
             </Link>
             <Link
               to="/tv"
               className="text-gray-300 hover:text-white transition"
             >
               TV Shows
             </Link>
             <Link
               to="/collections"
               className="text-gray-300 hover:text-white transition"
             >
               Collections
             </Link>
             <Link
               to="/requests"
               className="text-gray-300 hover:text-white transition"
             >
               Requests
             </Link>
             <Link
               to="/comments"
               className="text-gray-300 hover:text-white transition"
             >
               Comments
             </Link>
             <Link
               to="/video-progress"
               className="text-gray-300 hover:text-white transition"
             >
               Progress
             </Link>
             <Link
               to="/search"
               className="text-gray-300 hover:text-white transition"
             >
               Search
             </Link>
           </div>

          {/* User Menu */}
          <div className="flex items-center space-x-4">
            <Link
              to="/profile"
              className="text-sm text-gray-400 hover:text-white transition"
            >
              {user?.email}
            </Link>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}
