import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  userId: string | null
  login: (token: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      userId: null,
      login: (token) => set({ token }),
      logout: () => set({ token: null, userId: null }),
    }),
    { name: 'auth' }
  )
)
