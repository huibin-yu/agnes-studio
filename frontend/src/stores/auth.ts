import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: number
  email: string
  username: string
  avatar_url?: string
  credits: number
  is_verified: boolean
  referral_code?: string
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
 * Sets a non-httpOnly cookie that the Next.js middleware reads to gate
 * protected routes. The cookie only signals "logged in or not"; it does
 * NOT contain any token. This is a stop-gap until P1-4 moves tokens to
 * httpOnly cookies.
 */
function setAuthCookie(authenticated: boolean) {
  if (typeof document === 'undefined') return
  if (authenticated) {
    // 30-day expiry, matches refresh token lifetime
    document.cookie = 'agnes-auth=1; path=/; max-age=2592000; SameSite=Lax'
  } else {
    document.cookie = 'agnes-auth=; path=/; max-age=0; SameSite=Lax'
  }
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
      setAccessToken: (accessToken) => {
        set({ accessToken })
        setAuthCookie(accessToken !== null)
      },
      setRefreshToken: (refreshToken) => set({ refreshToken }),

      login: (accessToken, refreshToken, user) => {
        set({ accessToken, refreshToken, user })
        setAuthCookie(true)
      },

      logout: () => {
        set({ user: null, accessToken: null, refreshToken: null })
        setAuthCookie(false)
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
      onRehydrateStorage: () => (state) => {
        // Sync cookie with rehydrated state on page load
        if (state) {
          setAuthCookie(state.user !== null && state.accessToken !== null)
        }
      },
    }
  )
)

