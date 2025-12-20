import { create } from 'zustand';

export interface AssetType {
  id: number;
  name: string;
}

interface AssetTypesState {
  assetTypes: AssetType[];
  loading: boolean;
  error: string | null;
  fetchAssetTypes: () => Promise<void>;
  updateAssetType: (id: number, name: string) => Promise<void>;
  deleteAssetType: (id: number) => Promise<void>;
}

export const useAssetTypesStore = create<AssetTypesState>((set) => ({
  assetTypes: [],
  loading: false,
  error: null,

  fetchAssetTypes: async () => {
    set({ loading: true, error: null });
    try {
      const res = await fetch('/api/asset-types');
      if (!res.ok) throw new Error('Failed to fetch asset types');
      const data = await res.json();
      set({ assetTypes: data, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  updateAssetType: async (id: number, name: string) => {
    const token = localStorage.getItem('token');
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers.Authorization = `Bearer ${token}`;

    const res = await fetch(`/api/asset-types/${id}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify({ name }),
    });
    if (!res.ok) throw new Error('Failed to update asset type');
  },

  deleteAssetType: async (id: number) => {
    const token = localStorage.getItem('token');
    const headers: Record<string, string> = {};
    if (token) headers.Authorization = `Bearer ${token}`;

    const res = await fetch(`/api/asset-types/${id}`, {
      method: 'DELETE',
      headers,
    });
    if (!res.ok) throw new Error('Failed to delete asset type');
  },
}));
