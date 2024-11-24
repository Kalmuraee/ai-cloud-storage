import { create } from 'zustand';
import { Document, ProcessingStatus } from '../lib/api/types';

interface DocumentState {
  documents: Document[];
  selectedDocument: Document | null;
  processingTasks: Record<string, ProcessingStatus>;
  setDocuments: (documents: Document[]) => void;
  addDocument: (document: Document) => void;
  removeDocument: (documentId: number) => void;
  setSelectedDocument: (document: Document | null) => void;
  updateProcessingStatus: (taskId: string, status: ProcessingStatus) => void;
}

interface SearchState {
  searchQuery: string;
  searchResults: Document[];
  isSearching: boolean;
  setSearchQuery: (query: string) => void;
  setSearchResults: (results: Document[]) => void;
  setIsSearching: (isSearching: boolean) => void;
}

interface UIState {
  sidebarOpen: boolean;
  currentView: 'documents' | 'search' | 'chat';
  setSidebarOpen: (open: boolean) => void;
  setCurrentView: (view: 'documents' | 'search' | 'chat') => void;
}

export const useDocumentStore = create<DocumentState>((set) => ({
  documents: [],
  selectedDocument: null,
  processingTasks: {},
  setDocuments: (documents) => set({ documents }),
  addDocument: (document) =>
    set((state) => ({
      documents: [...state.documents, document],
    })),
  removeDocument: (documentId) =>
    set((state) => ({
      documents: state.documents.filter((doc) => doc.id !== documentId),
    })),
  setSelectedDocument: (document) => set({ selectedDocument: document }),
  updateProcessingStatus: (taskId, status) =>
    set((state) => ({
      processingTasks: {
        ...state.processingTasks,
        [taskId]: status,
      },
    })),
}));

export const useSearchStore = create<SearchState>((set) => ({
  searchQuery: '',
  searchResults: [],
  isSearching: false,
  setSearchQuery: (query) => set({ searchQuery: query }),
  setSearchResults: (results) => set({ searchResults: results }),
  setIsSearching: (isSearching) => set({ isSearching }),
}));

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  currentView: 'documents',
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setCurrentView: (view) => set({ currentView: view }),
}));
