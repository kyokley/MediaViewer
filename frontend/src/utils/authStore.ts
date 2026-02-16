import { create } from 'zustand'
import { User } from '@/types/api'
import { authAPI } from '@/utils/api'

export interface AuthStore {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  setUser: (user: User | null) => void
  clearError: () => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await authAPI.login({ username, password })
      const { access, refresh, user } = response.data

      localStorage.setItem('access_token', access)
      localStorage.setItem('refresh_token', refresh)

      set({
        user,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Login failed',
        isLoading: false,
      })
      throw error
    }
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
