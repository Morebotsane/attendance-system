import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Role } from '../types/api';
import { authApi } from '../api/auth';

interface AuthState {
  user: User | null;
  access_token: string | null;
  refresh_token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: User) => void;
}

// Derive role from backend's is_admin flag.
// Backend only has is_admin boolean — no manager role yet.
// When backend adds a role field, remove this mapping.
function deriveRole(is_admin: boolean): Role {
  return is_admin ? 'admin' : 'employee';
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      access_token: null,
      refresh_token: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (username, password) => {
        set({ isLoading: true });
        try {
          const data = await authApi.login(username, password);
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);

          // Map backend employee response to our User type
          const user: User = {
            ...data.employee,
            role: deriveRole(data.employee.is_admin),
          };

          set({
            user,
            access_token: data.access_token,
            refresh_token: data.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: async () => {
        try {
          await authApi.logout();
        } finally {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          set({
            user: null,
            access_token: null,
            refresh_token: null,
            isAuthenticated: false,
          });
        }
      },

      setUser: (user) => set({ user }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        access_token: state.access_token,
        refresh_token: state.refresh_token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
