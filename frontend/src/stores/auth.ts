import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: number
  email: string
  username: string
  avatar_url?: string
  credits: number
  is_verified: boolean
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null

  setUser: (user: User | null) => void
  setAccessToken: (token: string | null) => void
  setRefreshToken: (token: string | null) => void
  login: (accessToken: string, refreshToken: string, user: User) => void
  logout: () => void
  updateCredits: (credits: number) => void
}

/**
 * Derived selector: isAuthenticated is true when both user and accessToken exist.
 * Using a selector avoids the bug where an independent boolean flag falls out of
 * sync with the persisted state on page refresh.
 */
export const useIsAuthenticated = () =>
  useAuthStore((s) => s.user !== null && s.accessToken !== null)

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,

      setUser: (user) => set({ user }),
      setAccessToken: (accessToken) => set({ accessToken }),
      setRefreshToken: (refreshToken) => set({ refreshToken }),

      login: (accessToken, refreshToken, user) => {
        set({ accessToken, refreshToken, user })
      },

      logout: () => {
        set({ user: null, accessToken: null, refreshToken: null })
      },

      updateCredits: (credits) =>
        set((state) => ({
          user: state.user ? { ...state.user, credits } : null,
        })),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
)
