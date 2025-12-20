import { create } from 'zustand';

export interface SchemaField {
  id: number;
  schema_id: number;
  field_name: string;
  field_type: 'string' | 'integer' | 'float' | 'boolean' | 'date' | 'json' | 'array' | 'object';
  is_required: boolean;
  default_value?: string;
  constraints?: Record<string, any>;
  description?: string;
  is_deleted: boolean;
  order_index: number;
}

export interface Schema {
  id: number;
  name: string;
  version: number;
  asset_type_id: number;
  parent_schema_id?: number;
  allow_additional_fields: boolean;
  is_active: boolean;
  fields: SchemaField[];
  created_by: number;
  created_at: string;
  statistics?: {
    schema_id: number;
    record_count: number;
    field_count: number;
    last_updated: string;
  };
}

interface SchemaStore {
  schemas: Schema[];
  selectedSchema: Schema | null;
  loading: boolean;
  error: string | null;
  assetTypeId?: number;

  fetchSchemas: (assetTypeId?: number) => Promise<void>;
  fetchSchemaById: (id: number) => Promise<Schema | null>;
  createSchema: (data: {
    name: string;
    asset_type_id: number;
    fields: any[];
    allow_additional_fields?: boolean;
    parent_schema_id?: number;
  }) => Promise<Schema>;
  updateSchema: (id: number, data: { name?: string }) => Promise<void>;
  deleteSchema: (id: number) => Promise<void>;
  selectSchema: (schema: Schema | null) => void;

  addField: (schemaId: number, field: any) => Promise<void>;
  updateField: (schemaId: number, fieldName: string, updates: Partial<SchemaField>) => Promise<void>;
  deleteField: (schemaId: number, fieldName: string, permanent?: boolean) => Promise<void>;
  forkSchema: (schemaId: number, newName: string, modifications?: any) => Promise<Schema>;
}

const API_BASE = '/api';

const buildHeaders = (withJson = false) => {
  const headers: Record<string, string> = {};
  const token = localStorage.getItem('token');
  if (token) headers.Authorization = `Bearer ${token}`;
  if (withJson) headers['Content-Type'] = 'application/json';
  return headers;
};

export const useSchemaStore = create<SchemaStore>((set, get) => ({
  schemas: [],
  selectedSchema: null,
  loading: false,
  error: null,

  fetchSchemas: async (assetTypeId?: number) => {
    set({ loading: true, error: null });
    try {
      const params = new URLSearchParams();
      if (assetTypeId) params.append('asset_type_id', assetTypeId.toString());
      params.append('active_only', 'true');

      const url = `${API_BASE}/schemas?${params}`;
      const response = await fetch(url, { headers: buildHeaders() });
      if (!response.ok) throw new Error('Failed to fetch schemas');
      const data = await response.json();
      set({ schemas: data, assetTypeId, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  fetchSchemaById: async (id: number) => {
    try {
      const response = await fetch(`${API_BASE}/schemas/${id}`, {
        headers: buildHeaders(),
      });
      if (!response.ok) return null;
      return await response.json();
    } catch {
      return null;
    }
  },

  createSchema: async (data) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/schemas`, {
        method: 'POST',
        headers: buildHeaders(true),
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to create schema');
      const result = await response.json();
      set((state) => ({
        schemas: [...state.schemas, result.schema],
        loading: false,
      }));
      return result.schema;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
      throw error;
    }
  },

  updateSchema: async (id, data) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/schemas/${id}`, {
        method: 'PUT',
        headers: buildHeaders(true),
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to update schema');
      await get().fetchSchemas(get().assetTypeId);
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  deleteSchema: async (id) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/schemas/${id}`, {
        method: 'DELETE',
        headers: buildHeaders(),
      });
      if (!response.ok) throw new Error('Failed to delete schema');
      set((state) => ({
        schemas: state.schemas.filter((s) => s.id !== id),
        selectedSchema: state.selectedSchema?.id === id ? null : state.selectedSchema,
        loading: false,
      }));
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  selectSchema: (schema) => set({ selectedSchema: schema }),

  addField: async (schemaId, field) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/schemas/${schemaId}/fields`, {
        method: 'POST',
        headers: buildHeaders(true),
        body: JSON.stringify(field),
      });
      if (!response.ok) throw new Error('Failed to add field');
      await get().fetchSchemaById(schemaId);
      await get().fetchSchemas(get().assetTypeId);
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  updateField: async (schemaId, fieldName, updates) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/schemas/${schemaId}/fields/${fieldName}`, {
        method: 'PUT',
        headers: buildHeaders(true),
        body: JSON.stringify(updates),
      });
      if (!response.ok) throw new Error('Failed to update field');
      await get().fetchSchemas(get().assetTypeId);
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  deleteField: async (schemaId, fieldName, permanent = false) => {
    set({ loading: true, error: null });
    try {
      const url = `${API_BASE}/schemas/${schemaId}/fields/${fieldName}?permanent=${permanent}`;
      const response = await fetch(url, {
        method: 'DELETE',
        headers: buildHeaders(),
      });
      if (!response.ok) throw new Error('Failed to delete field');
      await get().fetchSchemas(get().assetTypeId);
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  forkSchema: async (schemaId, newName, modifications) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/schemas/${schemaId}/fork`, {
        method: 'POST',
        headers: buildHeaders(true),
        body: JSON.stringify({ name: newName, modifications }),
      });
      if (!response.ok) throw new Error('Failed to fork schema');
      const result = await response.json();
      set((state) => ({
        schemas: [...state.schemas, result.schema],
        loading: false,
      }));
      return result.schema;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
      throw error;
    }
  },
}));
