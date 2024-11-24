// Document Types
export interface Document {
  id: number;
  title: string;
  file_path: string;
  content_type: string;
  size: number;
  doc_metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface DocumentMetadata {
  id: number;
  title: string;
  status: string;
  content_type: string;
  size: number;
  metadata: Record<string, any>;
}

// Index Types
export interface IndexEntry {
  id: number;
  document_id: number;
  content: string;
  embedding: number[];
  index_metadata: Record<string, any>;
}

export interface IndexSearchResult {
  entry: IndexEntry;
  score: number;
  distance: number;
}

// Query Types
export interface QueryRequest {
  query: string;
  filters?: Record<string, any>;
  limit?: number;
}

export interface QueryResponse {
  results: any[];
  total: number;
  took: number;
}

// RAG Types
export interface RAGRequest {
  query: string;
  context?: string[];
  max_tokens?: number;
  temperature?: number;
}

export interface RAGResponse {
  response: string;
  sources: string[];
  confidence: number;
}

// Search Types
export interface SearchRequest {
  query: string;
  filters?: Record<string, any>;
  sort?: Record<string, string>;
  page?: number;
  limit?: number;
}

export interface SearchResult {
  document: Document;
  score: number;
  highlights: Record<string, string[]>;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  page: number;
  pages: number;
}

// Processing Types
export interface ProcessingRequest {
  document_id: number;
  options?: Record<string, any>;
}

export interface ProcessingStatus {
  status: string;
  progress: number;
  message?: string;
  errors?: string[];
}

// API Response Types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

// API Error
export interface ApiError {
  message: string;
  code: string;
  details?: Record<string, any>;
}
