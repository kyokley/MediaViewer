import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './utils/authStore'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import HomePage from './pages/HomePage'
import MoviesPage from './pages/MoviesPage'
import TVPage from './pages/TVPage'
import SearchPage from './pages/SearchPage'

function App() {
  const isAuthenticated = useAuthStore((state) => !!state.accessToken)

  return (
    <Router>
      <Routes>
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />}
        />
        <Route
          path="/"
          element={
            <ProtectedRoute isAuthenticated={isAuthenticated}>
              <HomePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/movies"
          element={
            <ProtectedRoute isAuthenticated={isAuthenticated}>
              <MoviesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/tv"
          element={
            <ProtectedRoute isAuthenticated={isAuthenticated}>
              <TVPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/search"
          element={
            <ProtectedRoute isAuthenticated={isAuthenticated}>
              <SearchPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  )
}

export default App
