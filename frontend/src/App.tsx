import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './utils/authStore'
import { PaginationProvider } from './context/PaginationContext'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import HomePage from './pages/HomePage'
import MoviesPage from './pages/MoviesPage'
import MovieDetailPage from './pages/MovieDetailPage'
import TVPage from './pages/TVPage'
import TVShowDetailPage from './pages/TVShowDetailPage'
import CollectionsPage from './pages/CollectionsPage'
import UserProfilePage from './pages/UserProfilePage'
import SearchPage from './pages/SearchPage'
import { RequestsPage } from './pages/RequestsPage'
import { CommentsPage } from './pages/CommentsPage'
import { VideoProgressPage } from './pages/VideoProgressPage'

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
              <PaginationProvider>
                <MoviesPage />
              </PaginationProvider>
            </ProtectedRoute>
          }
        />
        <Route
          path="/movies/:id"
          element={
            <ProtectedRoute isAuthenticated={isAuthenticated}>
              <MovieDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/tv"
          element={
            <ProtectedRoute isAuthenticated={isAuthenticated}>
              <PaginationProvider>
                <TVPage />
              </PaginationProvider>
            </ProtectedRoute>
          }
        />
        <Route
          path="/tv/:id"
          element={
            <ProtectedRoute isAuthenticated={isAuthenticated}>
              <TVShowDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/collections"
          element={
            <ProtectedRoute isAuthenticated={isAuthenticated}>
              <PaginationProvider>
                <CollectionsPage />
              </PaginationProvider>
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute isAuthenticated={isAuthenticated}>
              <UserProfilePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/search"
          element={
            <ProtectedRoute isAuthenticated={isAuthenticated}>
              <PaginationProvider>
                <SearchPage />
              </PaginationProvider>
            </ProtectedRoute>
          }
        />
        <Route
          path="/requests"
          element={
            <ProtectedRoute isAuthenticated={isAuthenticated}>
              <PaginationProvider>
                <RequestsPage />
              </PaginationProvider>
            </ProtectedRoute>
          }
        />
        <Route
          path="/comments"
          element={
            <ProtectedRoute isAuthenticated={isAuthenticated}>
              <PaginationProvider>
                <CommentsPage />
              </PaginationProvider>
            </ProtectedRoute>
          }
        />
        <Route
          path="/video-progress"
          element={
            <ProtectedRoute isAuthenticated={isAuthenticated}>
              <PaginationProvider>
                <VideoProgressPage />
              </PaginationProvider>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  )
}

export default App
