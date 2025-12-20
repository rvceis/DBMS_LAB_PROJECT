// API configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export const API_ENDPOINTS = {
  // Auth
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  
  // Users
  USERS_ME: '/users/me',
  USERS: '/users',
  
  // Asset Types
  ASSET_TYPES: '/asset-types',
  
  // Schemas
  SCHEMAS: '/schemas',
  
  // Metadata
  METADATA: '/metadata',
};
