import { create } from 'zustand';
import { documentAPI, storageAPI } from '@/lib/api';

interface FileState {
  files: any[];
  currentPath: string;
  isLoading: boolean;
  error: string | null;
  setFiles: (files: any[]) => void;
  setCurrentPath: (path: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  fetchFiles: (path?: string) => Promise<void>;
  uploadFile: (file: File, metadata?: Record<string, any>) => Promise<void>;
  deleteFile: (fileId: string) => Promise<void>;
  searchFiles: (query: string) => Promise<void>;
}

const useStore = create<FileState>((set, get) => ({
  files: [],
  currentPath: '/',
  isLoading: false,
  error: null,
  
  setFiles: (files) => set({ files }),
  setCurrentPath: (path) => set({ currentPath: path }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  
  fetchFiles: async (path = '/') => {
    try {
      set({ isLoading: true, error: null });
      const response = await storageAPI.listFiles(path);
      set({ files: response.files, currentPath: path });
    } catch (error: any) {
      set({ error: error.message });
    } finally {
      set({ isLoading: false });
    }
  },
  
  uploadFile: async (file: File, metadata?: Record<string, any>) => {
    try {
      set({ isLoading: true, error: null });
      await documentAPI.uploadDocument(file, metadata);
      await get().fetchFiles(get().currentPath);
    } catch (error: any) {
      set({ error: error.message });
    } finally {
      set({ isLoading: false });
    }
  },
  
  deleteFile: async (fileId: string) => {
    try {
      set({ isLoading: true, error: null });
      await documentAPI.deleteDocument(fileId);
      await get().fetchFiles(get().currentPath);
    } catch (error: any) {
      set({ error: error.message });
    } finally {
      set({ isLoading: false });
    }
  },
  
  searchFiles: async (query: string) => {
    try {
      set({ isLoading: true, error: null });
      const response = await documentAPI.searchDocuments(query);
      set({ files: response.results });
    } catch (error: any) {
      set({ error: error.message });
    } finally {
      set({ isLoading: false });
    }
  },
}));
