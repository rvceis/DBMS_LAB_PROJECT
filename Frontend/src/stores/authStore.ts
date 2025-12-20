import { create } from 'zustand';

interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'editor' | 'viewer';
}

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (username: string, email: string, password: string, role?: string) => Promise<void>;
  isAuthenticated: () => boolean;
  hasRole: (role: 'admin' | 'editor' | 'viewer') => boolean;
  setToken: (token: string) => void;
}

export const useAuthStore = create<AuthState>((set, get) => {
  // Restore token and user from localStorage on init
  const storedToken = localStorage.getItem('token');
  const storedUser = localStorage.getItem('user');

  return {
    user: storedUser ? JSON.parse(storedUser) : null,
    token: storedToken || null,
    loading: false,
    error: null,

    login: async (email: string, password: string) => {
      set({ loading: true, error: null });
      try {
        const response = await fetch(`/api/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ error: 'Login failed' }));
          throw new Error(errorData.error || 'Invalid credentials');
        }
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        set({ user: data.user, token: data.access_token, loading: false });
      } catch (error) {
        set({ error: (error as Error).message, loading: false });
        throw error;
      }
    },

    logout: () => {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      set({ user: null, token: null });
    },

    register: async (username: string, email: string, password: string, role = 'viewer') => {
      set({ loading: true, error: null });
      try {
        const response = await fetch(`/api/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, email, password, role }),
        });
        if (!response.ok) throw new Error('Registration failed');
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        set({ user: data.user, token: data.access_token, loading: false });
      } catch (error) {
        set({ error: (error as Error).message, loading: false });
        throw error;
      }
    },

    isAuthenticated: () => get().token !== null,
    hasRole: (role: string) => get().user?.role === role,
    setToken: (token: string) => {
      localStorage.setItem('token', token);
      set({ token });
    },
  };
});
