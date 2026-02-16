import { create } from 'zustand'
import { User } from '@/types/api'
import { authAPI } from '@/utils/api'

export interface AuthStore {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  accessToken: string | null
  refreshToken: string | null
  login: (accessToken: string, refreshToken: string, user?: User) => void
  logout: () => Promise<void>
  setUser: (user: User | null) => void
  clearError: () => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  accessToken: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),

  login: (accessToken: string, refreshToken: string, user?: User) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)

    set({
      accessToken,
      refreshToken,
      user: user || null,
      isAuthenticated: true,
      isLoading: false,
    })
  },

  logout: async () => {
    set({ isLoading: true, error: null })
    try {
      await authAPI.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        accessToken: null,
        refreshToken: null,
      })
    }
  },

  setUser: (user: User | null) => {
    set({
      user,
      isAuthenticated: user !== null,
    })
  },

  clearError: () => {
    set({ error: null })
  },
}))

// Helper to check if user is authenticated on app load
export const initializeAuth = async () => {
  const accessToken = localStorage.getItem('access_token')
  if (accessToken) {
    try {
      const response = await authAPI.getCurrentUser()
      useAuthStore.setState({
        user: response.data,
        isAuthenticated: true,
      })
    } catch (error) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      useAuthStore.setState({
        user: null,
        isAuthenticated: false,
      })
    }
  }
}
