import { create } from 'zustand';

interface UIState {
  theme: 'light' | 'dark' | 'system';
  sidebarOpen: boolean;
  toggleTheme: () => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
}

const getStoredTheme = (): 'light' | 'dark' | 'system' => {
  const stored = localStorage.getItem('theme');
  return (stored as 'light' | 'dark' | 'system') || 'system';
};

export const useUIStore = create<UIState>((set) => ({
  theme: getStoredTheme(),
  sidebarOpen: true,

  // Simple two-state toggle for smoother UX
  toggleTheme: () =>
    set((state) => {
      const newTheme = state.theme === 'dark' ? 'light' : 'dark';
      localStorage.setItem('theme', newTheme);
      return { theme: newTheme };
    }),

  setTheme: (theme) => {
    localStorage.setItem('theme', theme);
    set({ theme });
  },

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
}));
