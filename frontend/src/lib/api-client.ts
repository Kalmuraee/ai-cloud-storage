import axios from 'axios';

// Use relative URL for the API proxy
const API_BASE_URL = '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for API calls
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for API calls
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      // Handle token refresh or logout here
      return apiClient(originalRequest);
    }

    return Promise.reject(error);
  }
);

export interface FileUploadResponse {
  file_id: string;
  filename: string;
  size: number;
  content_type: string;
  upload_url: string;
}

export interface FileMetadata {
  id: string;
  name: string;
  size: number;
  type: string;
  uploaded_at: string;
  bucket: string;
}

export interface StorageAnalytics {
  total_size: number;
  file_count: number;
  bucket_stats: {
    [bucket: string]: {
      size: number;
      count: number;
    };
  };
}

export const api = {
  // File operations
  getUploadUrl: async (filename: string, contentType: string): Promise<FileUploadResponse> => {
    console.log('Requesting upload URL for:', { filename, contentType });
    try {
      const response = await apiClient.post('/files/upload-url', {
        filename,
        content_type: contentType,
      });
      
      console.log('Upload URL response:', response.data);
      
      if (!response.data) {
        throw new Error('No response data received from server');
      }
      
      // Ensure we have the required fields
      if (!response.data.upload_url) {
        console.error('Invalid response format:', response.data);
        throw new Error('Invalid response format from server');
      }
      
      // Ensure the upload_url is absolute
      const data = response.data;
      if (!data.upload_url.startsWith('http')) {
        data.upload_url = `${window.location.protocol}//${window.location.host}${data.upload_url}`;
      }
      
      return data;
    } catch (error) {
      console.error('Error getting upload URL:', error);
      if (axios.isAxiosError(error) && error.response) {
        console.error('Server response:', error.response.data);
        throw new Error(`Failed to get upload URL: ${error.response.data.message || error.message}`);
      }
      throw error;
    }
  },

  uploadFile: async (url: string, file: File): Promise<void> => {
    console.log('Starting file upload to:', url);
    try {
      const response = await fetch(url, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type,
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Upload failed:', {
          status: response.status,
          statusText: response.statusText,
          errorText,
        });
        throw new Error(`Upload failed: ${response.status} - ${errorText}`);
      }
      
      console.log('Upload completed successfully');
    } catch (error) {
      console.error('Upload error details:', error);
      throw error;
    }
  },

  listFiles: async (bucket?: string, prefix?: string): Promise<FileMetadata[]> => {
    const params = new URLSearchParams();
    if (bucket) params.append('bucket', bucket);
    if (prefix) params.append('prefix', prefix);
    
    const response = await apiClient.get(`/files?${params}`);
    return response.data;
  },

  deleteFile: async (fileId: string): Promise<void> => {
    await apiClient.delete(`/files/${fileId}`);
  },

  getDownloadUrl: async (fileId: string): Promise<string> => {
    const response = await apiClient.get(`/files/${fileId}/download-url`);
    return response.data.url;
  },

  // Storage analytics
  getStorageAnalytics: async (): Promise<StorageAnalytics> => {
    const response = await apiClient.get('/storage/analytics');
    return response.data;
  },

  // Bucket operations
  listBuckets: async (): Promise<string[]> => {
    const response = await apiClient.get('/buckets');
    return response.data;
  },

  createBucket: async (name: string): Promise<void> => {
    await apiClient.post('/buckets', { name });
  },

  deleteBucket: async (name: string): Promise<void> => {
    await apiClient.delete(`/buckets/${name}`);
  },
};

export default api;
