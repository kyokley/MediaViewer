import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../utils/authStore'
import ThemeToggle from './ThemeToggle'

export default function Navigation() {
  const navigate = useNavigate()
  const logout = useAuthStore((state) => state.logout)
  const user = useAuthStore((state) => state.user)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav
      className="fixed top-0 w-full border-b z-50"
      style={{
        backgroundColor: 'var(--bg-secondary)',
        borderColor: 'var(--border-primary)',
      }}
    >
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="text-2xl font-bold" style={{ color: 'var(--accent-primary)' }}>
              MV
            </div>
            <span className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
              MediaViewer
            </span>
          </Link>

           {/* Navigation Links */}
           <div className="hidden md:flex items-center space-x-8">
             <Link
               to="/"
               className="transition"
               style={{ color: 'var(--text-secondary)' }}
               onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
               onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}
             >
               Home
             </Link>
             <Link
               to="/movies"
               className="transition"
               style={{ color: 'var(--text-secondary)' }}
               onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
               onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}
             >
               Movies
             </Link>
             <Link
               to="/tv"
               className="transition"
               style={{ color: 'var(--text-secondary)' }}
               onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
               onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}
             >
               TV Shows
             </Link>
             <Link
               to="/collections"
               className="transition"
               style={{ color: 'var(--text-secondary)' }}
               onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
               onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}
             >
               Collections
             </Link>
             <Link
               to="/requests"
               className="transition"
               style={{ color: 'var(--text-secondary)' }}
               onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
               onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}
             >
               Requests
             </Link>
           </div>

          {/* User Menu */}
          <div className="flex items-center space-x-4">
            <ThemeToggle />
            <Link
              to="/profile"
              className="text-sm transition"
              style={{ color: 'var(--text-tertiary)' }}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-tertiary)')}
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
