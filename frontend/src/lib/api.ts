import axios from 'axios';
import { healthAPI } from './api/health';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // Add timeout and retry configuration
  timeout: 10000,
  timeoutErrorMessage: 'Request timeout',
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('accessToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (email: string, password: string) => {
    const response = await api.post('/api/v1/auth/login', { email, password });
    return response.data;
  },
  
  register: async (email: string, username: string, password: string, fullName: string) => {
    const response = await api.post('/api/v1/auth/register', {
      email,
      username,
      password,
      full_name: fullName,
    });
    return response.data;
  },
  
  getProfile: async () => {
    const response = await api.get('/api/v1/auth/profile');
    return response.data;
  },

  logout: async () => {
    localStorage.removeItem('accessToken');
    return true;
  },
};

// Document API
export const documentAPI = {
  uploadDocument: async (file: File, metadata?: Record<string, any>) => {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata));
    }
    
    const response = await api.post('/api/v1/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  listDocuments: async (params?: {
    page?: number;
    limit?: number;
    query?: string;
    sort?: string;
  }) => {
    const response = await api.get('/api/v1/documents', { params });
    return response.data;
  },

  getDocument: async (documentId: string) => {
    const response = await api.get(`/api/v1/documents/${documentId}`);
    return response.data;
  },

  deleteDocument: async (documentId: string) => {
    const response = await api.delete(`/api/v1/documents/${documentId}`);
    return response.data;
  },

  searchDocuments: async (query: string, options?: {
    page?: number;
    limit?: number;
    filters?: Record<string, any>;
  }) => {
    const response = await api.post('/api/v1/documents/search', {
      query,
      ...options,
    });
    return response.data;
  },
};

// Storage API
export const storageAPI = {
  getPresignedUrl: async (fileName: string, contentType: string) => {
    const response = await api.post('/api/v1/storage/presigned-url', {
      file_name: fileName,
      content_type: contentType,
    });
    return response.data;
  },

  listFiles: async (path: string = '/') => {
    const response = await api.get('/api/v1/storage/list', {
      params: { path },
    });
    return response.data;
  },
};

export { healthAPI };
export default api;
