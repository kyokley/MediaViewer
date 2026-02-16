import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorAlert from '../components/ErrorAlert'
import { useAuthStore } from '../utils/authStore'
import { apiClient } from '../utils/api'

export default function UserProfilePage() {
  const user = useAuthStore((state) => state.user)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const [formData, setFormData] = useState({
    dark_theme: true,
    items_per_page: 50,
    autoplay_next: false,
    default_quality: 'auto',
    subtitle_language: 'en',
    volume_level: 80,
    email_notifications: true,
  })

  useEffect(() => {
    const fetchSettings = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const response = await apiClient.get('/users/me/settings/')
        const settingsData = response.data.data
        setFormData({
          dark_theme: settingsData.dark_theme ?? true,
          items_per_page: settingsData.items_per_page ?? 50,
          autoplay_next: settingsData.autoplay_next ?? false,
          default_quality: settingsData.default_quality ?? 'auto',
          subtitle_language: settingsData.subtitle_language ?? 'en',
          volume_level: settingsData.volume_level ?? 80,
          email_notifications: settingsData.email_notifications ?? true,
        })
      } catch (err: any) {
        setError(
          err.response?.data?.error?.message ||
            'Failed to load settings'
        )
      } finally {
        setIsLoading(false)
      }
    }

    fetchSettings()
  }, [])

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, type } = e.target
    const value = type === 'checkbox' ? (e.target as HTMLInputElement).checked : e.target.value

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSaving(true)
    setError(null)
    setSuccess(false)

    try {
      await apiClient.put('/users/me/settings/', formData)
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err: any) {
      setError(
        err.response?.data?.error?.message ||
          'Failed to save settings'
      )
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <Layout>
        <LoadingSpinner />
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-8">Profile & Settings</h1>

        {/* User Profile Section */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-2xl font-bold text-white mb-6">Profile Information</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Username
              </label>
              <input
                type="text"
                value={user?.username || ''}
                disabled
                className="w-full px-4 py-2 bg-gray-700 text-gray-400 rounded-lg border border-gray-600 outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Email
              </label>
              <input
                type="email"
                value={user?.email || ''}
                disabled
                className="w-full px-4 py-2 bg-gray-700 text-gray-400 rounded-lg border border-gray-600 outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  First Name
                </label>
                <input
                  type="text"
                  value={user?.first_name || ''}
                  disabled
                  className="w-full px-4 py-2 bg-gray-700 text-gray-400 rounded-lg border border-gray-600 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Last Name
                </label>
                <input
                  type="text"
                  value={user?.last_name || ''}
                  disabled
                  className="w-full px-4 py-2 bg-gray-700 text-gray-400 rounded-lg border border-gray-600 outline-none"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Settings Section */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-2xl font-bold text-white mb-6">Preferences</h2>

          {error && <ErrorAlert message={error} />}

          {success && (
            <div className="mb-4 p-4 bg-green-900/50 border border-green-700 text-green-200 rounded-lg">
              Settings saved successfully!
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Theme */}
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="dark_theme"
                  checked={formData.dark_theme}
                  onChange={handleInputChange}
                  className="w-4 h-4 rounded border-gray-600 bg-gray-700 accent-blue-600"
                />
                <span className="ml-3 text-sm font-medium text-gray-300">
                  Dark Theme
                </span>
              </label>
            </div>

            {/* Items per Page */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Items Per Page
              </label>
              <select
                name="items_per_page"
                value={formData.items_per_page}
                onChange={handleInputChange}
                className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 outline-none"
              >
                <option value="10">10</option>
                <option value="20">20</option>
                <option value="50">50</option>
                <option value="100">100</option>
              </select>
            </div>

            {/* Autoplay Next */}
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="autoplay_next"
                  checked={formData.autoplay_next}
                  onChange={handleInputChange}
                  className="w-4 h-4 rounded border-gray-600 bg-gray-700 accent-blue-600"
                />
                <span className="ml-3 text-sm font-medium text-gray-300">
                  Autoplay Next Episode
                </span>
              </label>
            </div>

            {/* Default Quality */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Default Video Quality
              </label>
              <select
                name="default_quality"
                value={formData.default_quality}
                onChange={handleInputChange}
                className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 outline-none"
              >
                <option value="auto">Auto</option>
                <option value="1080p">1080p</option>
                <option value="720p">720p</option>
                <option value="480p">480p</option>
              </select>
            </div>

            {/* Subtitle Language */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Subtitle Language
              </label>
              <select
                name="subtitle_language"
                value={formData.subtitle_language}
                onChange={handleInputChange}
                className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 outline-none"
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="ja">Japanese</option>
                <option value="none">None</option>
              </select>
            </div>

            {/* Volume Level */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Default Volume Level: {formData.volume_level}%
              </label>
              <input
                type="range"
                name="volume_level"
                min="0"
                max="100"
                value={formData.volume_level}
                onChange={handleInputChange}
                className="w-full"
              />
            </div>

            {/* Email Notifications */}
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="email_notifications"
                  checked={formData.email_notifications}
                  onChange={handleInputChange}
                  className="w-4 h-4 rounded border-gray-600 bg-gray-700 accent-blue-600"
                />
                <span className="ml-3 text-sm font-medium text-gray-300">
                  Email Notifications
                </span>
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSaving}
              className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg font-medium transition"
            >
              {isSaving ? 'Saving...' : 'Save Settings'}
            </button>
          </form>
        </div>
      </div>
    </Layout>
  )
}
