import axios from 'axios';
import { API_BASE_URL, ERROR_MESSAGES, SUCCESS_MESSAGES } from '@/config';

const api = axios.create({
  baseURL: `${API_BASE_URL}/storage`,
  withCredentials: true,
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with a status code outside of 2xx
      const message = error.response.data?.detail || ERROR_MESSAGES.NETWORK_ERROR;
      throw new Error(message);
    } else if (error.request) {
      // Request was made but no response received
      throw new Error(ERROR_MESSAGES.NETWORK_ERROR);
    } else {
      // Something else happened while setting up the request
      throw new Error(error.message || ERROR_MESSAGES.NETWORK_ERROR);
    }
  }
);

export interface FileUploadResponse {
  file: {
    id: number;
    filename: string;
    path: string;
    size: number;
    content_type: string;
    owner_id: number;
    created_at: string;
    updated_at?: string;
  };
  is_duplicate: boolean;
}

export interface FileMetadata {
  id: number;
  filename: string;
  path: string;
  size: number;
  content_type: string;
  owner_id: number;
  created_at: string;
  updated_at?: string;
  metadata: Record<string, any>;
}

export interface DuplicateFile {
  content_hash: string;
  files: FileMetadata[];
}

export interface StorageAnalytics {
  totalSize: number;
  totalFiles: number;
  savedSpace: number;
  duplicateFiles: number;
  fileTypes: {
    extension: string;
    count: number;
  }[];
}

export const storageApi = {
  // Upload file with deduplication
  uploadFile: async (file: File, folderId?: number, checkDuplicates: boolean = true) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (folderId) formData.append('folder_id', folderId.toString());
      formData.append('check_duplicates', checkDuplicates.toString());

      const response = await api.post<FileUploadResponse>('/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : ERROR_MESSAGES.UPLOAD_FAILED);
    }
  },

  // List all files
  listFiles: async (prefix?: string, recursive: boolean = true) => {
    try {
      const params = new URLSearchParams();
      if (prefix) params.append('prefix', prefix);
      params.append('recursive', recursive.toString());

      const response = await api.get('/files/', { params });
      return response.data;
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : ERROR_MESSAGES.NETWORK_ERROR);
    }
  },

  // Get file metadata
  getFileMetadata: async (filePath: string) => {
    try {
      const response = await api.get<FileMetadata>(`/${filePath}/metadata`);
      return response.data;
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : ERROR_MESSAGES.NETWORK_ERROR);
    }
  },

  // Update file metadata
  updateMetadata: async (filePath: string, metadata: Record<string, any>) => {
    try {
      const response = await api.patch(`/${filePath}/metadata`, { metadata });
      return response.data;
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : ERROR_MESSAGES.NETWORK_ERROR);
    }
  },

  // Get duplicate files
  getDuplicates: async () => {
    try {
      const response = await api.get<DuplicateFile[]>('/duplicates/');
      return response.data;
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : ERROR_MESSAGES.NETWORK_ERROR);
    }
  },

  // Download file
  downloadFile: async (filePath: string) => {
    try {
      const response = await api.get(`/${filePath}`, {
        responseType: 'blob',
      });
      return response.data;
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : ERROR_MESSAGES.DOWNLOAD_FAILED);
    }
  },

  // Delete file
  deleteFile: async (filePath: string) => {
    try {
      const response = await api.delete(`/${filePath}`);
      return response.data;
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : ERROR_MESSAGES.DELETE_FAILED);
    }
  },

  // Create folder
  createFolder: async (name: string, parentId?: number) => {
    try {
      const response = await api.post('/folders/', {
        name,
        parent_id: parentId,
      });
      return response.data;
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : ERROR_MESSAGES.NETWORK_ERROR);
    }
  },

  // List folders
  listFolders: async () => {
    try {
      const response = await api.get('/folders/');
      return response.data;
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : ERROR_MESSAGES.NETWORK_ERROR);
    }
  },

  // Move file/folder
  moveItem: async (itemPath: string, destinationFolderId?: number) => {
    try {
      const response = await api.post(`/${itemPath}/move`, {
        destination_folder_id: destinationFolderId,
      });
      return response.data;
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : ERROR_MESSAGES.NETWORK_ERROR);
    }
  },

  // Share file/folder
  shareItem: async (itemPath: string, email?: string, permissions: string[] = ['read']) => {
    try {
      const response = await api.post(`/${itemPath}/share`, {
        email,
        permissions,
      });
      return response.data;
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : ERROR_MESSAGES.NETWORK_ERROR);
    }
  },

  // Get storage analytics
  async getAnalytics(): Promise<StorageAnalytics> {
    try {
      const response = await axios.get<StorageAnalytics>(`${API_BASE_URL}/storage/analytics`);
      return response.data;
    } catch (error) {
      throw new Error('Failed to fetch storage analytics');
    }
  },
};
