import { create } from 'zustand';

export interface ReportTemplate {
  id: number;
  name: string;
  description?: string;
  schema_id: number;
  asset_type_id?: number;
  query_config: QueryConfig;
  display_config: DisplayConfig;
  pdf_config: PdfConfig;
  created_by: number;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface QueryConfig {
  fields: string[];
  filters: FilterDef[];
  sort: SortDef[];
  limit?: number;
}

export interface FilterDef {
  field: string;
  operator: 'eq' | 'ne' | 'gt' | 'lt' | 'gte' | 'lte' | 'in' | 'contains' | 'between';
  value: any;
}

export interface SortDef {
  field: string;
  direction: 'asc' | 'desc';
}

export interface DisplayConfig {
  title?: string;
  column_labels?: Record<string, string>;
}

export interface PdfConfig {
  orientation?: 'portrait' | 'landscape';
  page_size?: 'A4' | 'Letter';
  title?: string;
  show_metadata?: boolean;
}

export interface ReportExecution {
  id: number;
  template_id?: number;
  template_name?: string;
  user_id: number;
  trigger_type: string;
  started_at: string;
  completed_at?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  format: 'csv' | 'pdf';
  row_count?: number;
  file_path?: string;
  file_size?: number;
  error_message?: string;
  execution_time_ms?: number;
}

interface ReportState {
  templates: ReportTemplate[];
  executions: ReportExecution[];
  selectedTemplate: ReportTemplate | null;
  loading: boolean;
  error: string | null;
  
  // Actions
  fetchTemplates: () => Promise<void>;
  fetchTemplate: (id: number) => Promise<void>;
  createTemplate: (data: Partial<ReportTemplate>) => Promise<ReportTemplate>;
  updateTemplate: (id: number, data: Partial<ReportTemplate>) => Promise<void>;
  deleteTemplate: (id: number) => Promise<void>;
  
  generateReport: (templateId: number, format: 'csv' | 'pdf', params?: any) => Promise<ReportExecution>;
  generateAdhocReport: (schemaId: number, queryConfig: QueryConfig, format: 'csv' | 'pdf', name?: string) => Promise<ReportExecution>;
  
  fetchExecutions: () => Promise<void>;
  fetchExecution: (id: number) => Promise<ReportExecution>;
  downloadReport: (executionId: number) => Promise<void>;
  deleteExecution: (id: number) => Promise<void>;
  
  selectTemplate: (template: ReportTemplate | null) => void;
}

const API_BASE = '/api/reports';

const buildHeaders = (withJson = false) => {
  const headers: Record<string, string> = {};
  const token = localStorage.getItem('token');
  if (token) headers.Authorization = `Bearer ${token}`;
  if (withJson) headers['Content-Type'] = 'application/json';
  return headers;
};

export const useReportStore = create<ReportState>((set, get) => ({
  templates: [],
  executions: [],
  selectedTemplate: null,
  loading: false,
  error: null,
  
  fetchTemplates: async () => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/templates`, {
        headers: buildHeaders(),
      });
      if (!response.ok) throw new Error('Failed to fetch templates');
      const data = await response.json();
      set({ templates: data, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },
  
  fetchTemplate: async (id: number) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/templates/${id}`, {
        headers: buildHeaders(),
      });
      if (!response.ok) throw new Error('Failed to fetch template');
      const data = await response.json();
      set({ selectedTemplate: data, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },
  
  createTemplate: async (data: Partial<ReportTemplate>) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/templates`, {
        method: 'POST',
        headers: buildHeaders(true),
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to create template');
      const result = await response.json();
      set((state) => ({
        templates: [...state.templates, result],
        loading: false,
      }));
      return result;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
      throw error;
    }
  },
  
  updateTemplate: async (id: number, data: Partial<ReportTemplate>) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/templates/${id}`, {
        method: 'PUT',
        headers: buildHeaders(true),
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to update template');
      const result = await response.json();
      set((state) => ({
        templates: state.templates.map((t) => (t.id === id ? result : t)),
        selectedTemplate: state.selectedTemplate?.id === id ? result : state.selectedTemplate,
        loading: false,
      }));
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },
  
  deleteTemplate: async (id: number) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/templates/${id}`, {
        method: 'DELETE',
        headers: buildHeaders(),
      });
      if (!response.ok) throw new Error('Failed to delete template');
      set((state) => ({
        templates: state.templates.filter((t) => t.id !== id),
        selectedTemplate: state.selectedTemplate?.id === id ? null : state.selectedTemplate,
        loading: false,
      }));
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },
  
  generateReport: async (templateId: number, format: 'csv' | 'pdf', params?: any) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/generate`, {
        method: 'POST',
        headers: buildHeaders(true),
        body: JSON.stringify({ template_id: templateId, format, params }),
      });
      if (!response.ok) throw new Error('Failed to generate report');
      const result = await response.json();
      set({ loading: false });
      return result;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
      throw error;
    }
  },
  
  generateAdhocReport: async (schemaId: number, queryConfig: QueryConfig, format: 'csv' | 'pdf', name?: string) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/generate/adhoc`, {
        method: 'POST',
        headers: buildHeaders(true),
        body: JSON.stringify({ schema_id: schemaId, query_config: queryConfig, format, name }),
      });
      if (!response.ok) throw new Error('Failed to generate report');
      const result = await response.json();
      set({ loading: false });
      return result;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
      throw error;
    }
  },
  
  fetchExecutions: async () => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/executions`, {
        headers: buildHeaders(),
      });
      if (!response.ok) throw new Error('Failed to fetch executions');
      const data = await response.json();
      set({ executions: data, loading: false });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },
  
  fetchExecution: async (id: number) => {
    try {
      const response = await fetch(`${API_BASE}/executions/${id}`, {
        headers: buildHeaders(),
      });
      if (!response.ok) throw new Error('Failed to fetch execution');
      return await response.json();
    } catch (error) {
      throw error;
    }
  },
  
  downloadReport: async (executionId: number) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }
      
      const response = await fetch(`${API_BASE}/executions/${executionId}/download`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        credentials: 'include',
      });
      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Unauthorized: Please log in again');
        }
        throw new Error(`Failed to download report: ${response.statusText}`);
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      // Extract filename from content-disposition header
      const contentDisposition = response.headers.get('content-disposition');
      let filename = `report_${executionId}`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+?)"?$/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1];
        }
      }
      
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      throw error;
    }
  },
  
  deleteExecution: async (id: number) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/executions/${id}`, {
        method: 'DELETE',
        headers: buildHeaders(),
      });
      if (!response.ok) throw new Error('Failed to delete execution');
      set((state) => ({
        executions: state.executions.filter((e) => e.id !== id),
        loading: false,
      }));
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },
  
  selectTemplate: (template: ReportTemplate | null) => set({ selectedTemplate: template }),
}));
