import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../config/api';

export const assetTypeService = {
  async getAll() {
    return apiClient.get(API_ENDPOINTS.ASSET_TYPES);
  },

  async create(name) {
    return apiClient.post(API_ENDPOINTS.ASSET_TYPES, { name });
  },

  async update(id, name) {
    return apiClient.put(`${API_ENDPOINTS.ASSET_TYPES}/${id}`, { name });
  },

  async delete(id) {
    return apiClient.delete(`${API_ENDPOINTS.ASSET_TYPES}/${id}`);
  },
};

export const schemaService = {
  async getAll() {
    return apiClient.get(API_ENDPOINTS.SCHEMAS);
  },

  // Legacy create (JSON Schema) - kept for backward compatibility if backend supports it
  async createLegacy(schemaJson) {
    return apiClient.post(API_ENDPOINTS.SCHEMAS, { schema_json: schemaJson });
  },

  // Dynamic schema create
  async createDynamic({ name, asset_type_id, fields, allow_additional_fields = true, parent_schema_id = null }) {
    return apiClient.post(API_ENDPOINTS.SCHEMAS, {
      name,
      asset_type_id,
      fields,
      allow_additional_fields,
      parent_schema_id,
    });
  },

  async getById(id) {
    return apiClient.get(`${API_ENDPOINTS.SCHEMAS}/${id}`);
  },
};

export const metadataService = {
  async getAll(params = {}) {
    return apiClient.get(API_ENDPOINTS.METADATA, params);
  },

  async getById(id) {
    return apiClient.get(`${API_ENDPOINTS.METADATA}/${id}`);
  },

  async create(data) {
    return apiClient.post(API_ENDPOINTS.METADATA, data);
  },

  async update(id, data) {
    return apiClient.put(`${API_ENDPOINTS.METADATA}/${id}`, data);
  },

  async delete(id) {
    return apiClient.delete(`${API_ENDPOINTS.METADATA}/${id}`);
  },
};

export const userService = {
  async getMe() {
    return apiClient.get(API_ENDPOINTS.USERS_ME);
  },

  async getAll() {
    return apiClient.get(API_ENDPOINTS.USERS);
  },
};
