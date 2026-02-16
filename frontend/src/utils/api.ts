import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { LoginRequest, LoginResponse, RefreshTokenRequest, RefreshTokenResponse } from '@/types/api'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: '/api/v2',
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

        const response = await axios.post<RefreshTokenResponse>(
          '/api/v2/auth/refresh/',
          { refresh: refreshToken } as RefreshTokenRequest
        )

        const { access, refresh } = response.data
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

export default api

// Authentication API functions
export const authAPI = {
  login: (credentials: LoginRequest) =>
    axios.post<LoginResponse>('/api/v2/auth/login/', credentials),

  logout: () =>
    api.post('/api/v2/auth/logout/'),

  getCurrentUser: () =>
    api.get('/api/v2/auth/me/'),

  refreshToken: (refreshToken: string) =>
    axios.post<RefreshTokenResponse>('/api/v2/auth/refresh/', {
      refresh: refreshToken,
    } as RefreshTokenRequest),
}

// User API functions
export const userAPI = {
  getProfile: () =>
    api.get('/api/v2/users/me/'),

  updateProfile: (data: Record<string, unknown>) =>
    api.put('/api/v2/users/me/', data),

  getSettings: () =>
    api.get('/api/v2/users/me/settings/'),

  updateSettings: (data: Record<string, unknown>) =>
    api.put('/api/v2/users/me/settings/', data),
}

// Media API functions
export const mediaAPI = {
  getMovies: (limit = 50, offset = 0, search = '') =>
    api.get('/api/v2/movies/', { params: { limit, offset, search } }),

  getMovie: (id: number) =>
    api.get(`/api/v2/movies/${id}/`),

  getTVShows: (limit = 50, offset = 0, search = '') =>
    api.get('/api/v2/tv/', { params: { limit, offset, search } }),

  getTVShow: (id: number) =>
    api.get(`/api/v2/tv/${id}/`),

  getGenres: (limit = 50, offset = 0, mediaType = '') =>
    api.get('/api/v2/genres/', { params: { limit, offset, media_type: mediaType } }),

  search: (query: string, type = '', limit = 20) =>
    api.get('/api/v2/search/', { params: { q: query, type, limit } }),
}

// Collection API functions
export const collectionAPI = {
  getCollections: (limit = 50, offset = 0) =>
    api.get('/api/v2/collections/', { params: { limit, offset } }),

  getCollection: (id: number) =>
    api.get(`/api/v2/collections/${id}/`),

  createCollection: (data: Record<string, unknown>) =>
    api.post('/api/v2/collections/', data),

  updateCollection: (id: number, data: Record<string, unknown>) =>
    api.put(`/api/v2/collections/${id}/`, data),

  deleteCollection: (id: number) =>
    api.delete(`/api/v2/collections/${id}/`),

  getCollectionItems: (id: number) =>
    api.get(`/api/v2/collections/${id}/items/`),
}

// Request API functions
export const requestAPI = {
  getRequests: (limit = 50, offset = 0) =>
    api.get('/api/v2/requests/', { params: { limit, offset } }),

  getRequest: (id: number) =>
    api.get(`/api/v2/requests/${id}/`),

  createRequest: (data: Record<string, unknown>) =>
    api.post('/api/v2/requests/', data),

  updateRequest: (id: number, data: Record<string, unknown>) =>
    api.put(`/api/v2/requests/${id}/`, data),

  deleteRequest: (id: number) =>
    api.delete(`/api/v2/requests/${id}/`),
}

// Video progress API functions
export const videoProgressAPI = {
  getProgress: (limit = 50, offset = 0) =>
    api.get('/api/v2/video-progress/', { params: { limit, offset } }),

  saveProgress: (data: Record<string, unknown>) =>
    api.post('/api/v2/video-progress/', data),

  deleteProgress: (hashedFilename: string) =>
    api.delete(`/api/v2/video-progress/${hashedFilename}/`),
}

// Comment API functions
export const commentAPI = {
  getComments: (limit = 50, offset = 0) =>
    api.get('/api/v2/comments/', { params: { limit, offset } }),

  getComment: (id: number) =>
    api.get(`/api/v2/comments/${id}/`),

  createComment: (data: Record<string, unknown>) =>
    api.post('/api/v2/comments/', data),

  updateComment: (id: number, data: Record<string, unknown>) =>
    api.put(`/api/v2/comments/${id}/`, data),

  deleteComment: (id: number) =>
    api.delete(`/api/v2/comments/${id}/`),
}
