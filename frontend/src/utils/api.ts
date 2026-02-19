import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { LoginRequest, LoginResponse, RefreshTokenRequest, RefreshTokenResponse } from '@/types/api'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: '/mediaviewer/api/v2',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add JWT token
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) {
          throw new Error('No refresh token available')
        }

         const response = await axios.post<{ data: RefreshTokenResponse }>(
           '/mediaviewer/api/v2/auth/refresh/',
           { refresh: refreshToken } as RefreshTokenRequest
         )

        const { access, refresh } = response.data.data
        localStorage.setItem('access_token', access)
        if (refresh) {
          localStorage.setItem('refresh_token', refresh)
        }

        // Retry original request
        api.defaults.headers.common['Authorization'] = `Bearer ${access}`
        originalRequest.headers.Authorization = `Bearer ${access}`

        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export { api as apiClient }
export default api

// Authentication API functions
export const authAPI = {
  login: (credentials: LoginRequest) =>
    axios.post<LoginResponse>('/mediaviewer/api/v2/auth/login/', credentials),

  logout: () =>
    api.post('/auth/logout/'),

  getCurrentUser: () =>
    api.get('/auth/me/'),

  refreshToken: (refreshToken: string) =>
    axios.post<RefreshTokenResponse>('/mediaviewer/api/v2/auth/refresh/', {
      refresh: refreshToken,
    } as RefreshTokenRequest),
}

// User API functions
export const userAPI = {
  getProfile: () =>
    api.get('/users/me/'),

  updateProfile: (data: Record<string, unknown>) =>
    api.put('/users/me/', data),

  getSettings: () =>
    api.get('/users/me/settings/'),

  updateSettings: (data: Record<string, unknown>) =>
    api.put('/users/me/settings/', data),
}

// Media API functions
export const mediaAPI = {
  getMovies: (limit = 50, offset = 0, search = '') =>
    api.get('/movies/', { params: { limit, offset, search } }),

  getMovie: (id: number) =>
    api.get(`/movies/${id}/`),

  getTVShows: (limit = 50, offset = 0, search = '') =>
    api.get('/tv/', { params: { limit, offset, search } }),

  getTVShow: (id: number) =>
    api.get(`/tv/${id}/`),

  getGenres: (limit = 50, offset = 0, mediaType = '') =>
    api.get('/genres/', { params: { limit, offset, media_type: mediaType } }),

  search: (query: string, type = '', limit = 20) =>
    api.get('/search/', { params: { q: query, type, limit } }),
}

// Collection API functions
export const collectionAPI = {
  getCollections: (limit = 50, offset = 0) =>
    api.get('/collections/', { params: { limit, offset } }),

  getCollection: (id: number) =>
    api.get(`/collections/${id}/`),

  createCollection: (data: Record<string, unknown>) =>
    api.post('/collections/', data),

  updateCollection: (id: number, data: Record<string, unknown>) =>
    api.put(`/collections/${id}/`, data),

  deleteCollection: (id: number) =>
    api.delete(`/collections/${id}/`),

  getCollectionItems: (id: number) =>
    api.get(`/collections/${id}/items/`),
}

// Request API functions
export const requestAPI = {
  getRequests: (limit = 20, offset = 0) =>
    api.get('/requests/', { params: { limit, offset } }),

  getRequest: (id: number) =>
    api.get(`/requests/${id}/`),

  createRequest: (data: Record<string, unknown>) =>
    api.post('/requests/', data),

  updateRequest: (id: number, data: Record<string, unknown>) =>
    api.put(`/requests/${id}/`, data),

  deleteRequest: (id: number) =>
    api.delete(`/requests/${id}/`),

  voteRequest: (id: number) =>
    api.post(`/requests/${id}/vote/`),

  markRequestDone: (id: number) =>
    api.post(`/requests/${id}/done/`),
}

// Video progress API functions
export const videoProgressAPI = {
  getProgress: (limit = 50, offset = 0) =>
    api.get('/video-progress/', { params: { limit, offset } }),

  saveProgress: (data: Record<string, unknown>) =>
    api.post('/video-progress/', data),

  deleteProgress: (hashedFilename: string) =>
    api.delete(`/video-progress/${hashedFilename}/`),
}

// Comment API functions
export const commentAPI = {
  getComments: (limit = 50, offset = 0) =>
    api.get('/comments/', { params: { limit, offset } }),

  getComment: (id: number) =>
    api.get(`/comments/${id}/`),

  createComment: (data: Record<string, unknown>) =>
    api.post('/comments/', data),

  updateComment: (id: number, data: Record<string, unknown>) =>
    api.put(`/comments/${id}/`, data),

  deleteComment: (id: number) =>
    api.delete(`/comments/${id}/`),
}
