import { create } from 'zustand';

export interface MetadataRecord {
  id: number;
  name: string;
  schema_id: number;
  asset_type_id?: number;
  asset_type_name?: string;
  values: Record<string, any>;
  tag?: string;
  created_by: number;
  created_by_name?: string;
  created_at: string;
  updated_at?: string;
}

export interface MetadataFilters {
  asset_type_id?: number;
  schema_id?: number;
  tag?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

interface MetadataStore {
  records: MetadataRecord[];
  selectedRecord: MetadataRecord | null;
  filters: MetadataFilters;
  loading: boolean;
  error: string | null;
  total: number;

  fetchRecords: (filters?: MetadataFilters) => Promise<void>;
  fetchRecordById: (id: number) => Promise<MetadataRecord | null>;
  createRecord: (data: {
    name: string;
    schema_id?: number;
    asset_type_id: number;
    values: Record<string, any>;
    create_new_schema?: boolean;
    tag?: string;
  }) => Promise<MetadataRecord>;
  updateRecord: (id: number, data: Partial<MetadataRecord>) => Promise<void>;
  deleteRecord: (id: number) => Promise<void>;
  selectRecord: (record: MetadataRecord | null) => void;
  setFilters: (filters: Partial<MetadataFilters>) => void;
  suggestSchemas: (values: Record<string, any>, assetTypeId?: number) => Promise<any[]>;
}

const API_BASE = '/api';

const buildHeaders = (withJson = false) => {
  const headers: Record<string, string> = {};
  const token = localStorage.getItem('token');
  if (token) headers.Authorization = `Bearer ${token}`;
  if (withJson) headers['Content-Type'] = 'application/json';
  return headers;
};

export const useMetadataStore = create<MetadataStore>((set, get) => ({
  records: [],
  selectedRecord: null,
  filters: { limit: 50, offset: 0 },
  loading: false,
  error: null,
  total: 0,

  fetchRecords: async (filters = {}) => {
    set({ loading: true, error: null });
    try {
      const params = new URLSearchParams();
      const mergedFilters = { ...get().filters, ...filters };
      if (mergedFilters.asset_type_id) params.append('asset_type', mergedFilters.asset_type_id.toString());
      if (mergedFilters.search) params.append('search', mergedFilters.search);
      if (mergedFilters.limit) params.append('limit', mergedFilters.limit.toString());

      const response = await fetch(`${API_BASE}/metadata?${params}`, {
        headers: buildHeaders(),
      });
      if (!response.ok) throw new Error('Failed to fetch records');
      const data = await response.json();
      set({ records: data, loading: false, filters: mergedFilters });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  fetchRecordById: async (id: number) => {
    try {
      const response = await fetch(`${API_BASE}/metadata/${id}`, {
        headers: buildHeaders(),
      });
      if (!response.ok) return null;
      return await response.json();
    } catch {
      return null;
    }
  },

  createRecord: async (data) => {
    set({ loading: true, error: null });
    try {
      const payload: any = {
        ...data,
      };
      if (data.create_new_schema && payload.allow_additional_fields === undefined) {
        payload.allow_additional_fields = true;
      }

      const response = await fetch(`${API_BASE}/metadata`, {
        method: 'POST',
        headers: buildHeaders(true),
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        let message = 'Failed to create record';
        try {
          const err = await response.json();
          if (err?.error) message = err.error;
        } catch {
          // fallback to text if json not available
          try {
            const errText = await response.text();
            if (errText) message = errText;
          } catch {}
        }
        throw new Error(message);
      }
      const result = await response.json();
      set((state) => ({
        records: [result, ...state.records],
        loading: false,
      }));
      return result;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
      throw error;
    }
  },

  updateRecord: async (id, data) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/metadata/${id}`, {
        method: 'PUT',
        headers: buildHeaders(true),
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to update record');
      await get().fetchRecords(get().filters);
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  deleteRecord: async (id) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/metadata/${id}`, {
        method: 'DELETE',
        headers: buildHeaders(),
      });
      if (!response.ok) throw new Error('Failed to delete record');
      set((state) => ({
        records: state.records.filter((r) => r.id !== id),
        selectedRecord: state.selectedRecord?.id === id ? null : state.selectedRecord,
        loading: false,
      }));
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  selectRecord: (record) => set({ selectedRecord: record }),
  setFilters: (filters) => set((state) => ({ filters: { ...state.filters, ...filters } })),

  suggestSchemas: async (values, assetTypeId) => {
    try {
      const response = await fetch(`${API_BASE}/metadata/suggest-schemas`, {
        method: 'POST',
        headers: buildHeaders(true),
        body: JSON.stringify({ values, asset_type_id: assetTypeId }),
      });
      if (!response.ok) return [];
      const data = await response.json();
      return data.suggested_schemas || [];
    } catch {
      return [];
    }
  },
}));
