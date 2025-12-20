import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../config/api';

export const authService = {
  async login(email, password) {
    const response = await apiClient.post(API_ENDPOINTS.LOGIN, { email, password });
    if (response.access_token) {
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
    }
    return response;
  },

  async register(username, email, password, role = 'viewer') {
    const response = await apiClient.post(API_ENDPOINTS.REGISTER, {
      username,
      email,
      password,
      role,
    });
    if (response.access_token) {
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
    }
    return response;
  },

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  getToken() {
    return localStorage.getItem('token');
  },

  isAuthenticated() {
    return !!this.getToken();
  },
};
