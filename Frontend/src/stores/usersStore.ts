import { create } from 'zustand';

export interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'editor' | 'viewer';
}

interface UsersState {
  users: User[];
  loading: boolean;
  error: string | null;
  fetchUsers: () => Promise<void>;
}

const API_BASE = '/api';

const buildHeaders = () => {
  const headers: Record<string, string> = {};
  const token = localStorage.getItem('token');
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
};

export const useUsersStore = create<UsersState>((set) => ({
  users: [],
  loading: false,
  error: null,

  fetchUsers: async () => {
    set({ loading: true, error: null });
    try {
      const res = await fetch(`${API_BASE}/users`, {
        headers: buildHeaders(),
      });
      if (!res.ok) throw new Error('Failed to fetch users');
      const data = await res.json();
      set({ users: data, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },
}));
