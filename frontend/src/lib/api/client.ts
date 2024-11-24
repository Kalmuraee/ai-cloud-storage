import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  ApiResponse,
  Document,
  DocumentMetadata,
  IndexEntry,
  IndexSearchResult,
  QueryRequest,
  QueryResponse,
  RAGRequest,
  RAGResponse,
  SearchRequest,
  SearchResponse,
  ProcessingRequest,
  ProcessingStatus,
} from './types';

class ApiClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for consistent error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        const errorResponse: ApiResponse<null> = {
          error: error.response?.data?.detail || 'An unexpected error occurred',
          status: error.response?.status || 500,
        };
        return Promise.reject(errorResponse);
      }
    );
  }

  // Document Management
  async uploadDocument(file: File, process: boolean = true): Promise<ApiResponse<DocumentMetadata>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('process', String(process));

    const response = await this.client.post<DocumentMetadata>('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return { data: response.data, status: response.status };
  }

  async processDocument(documentId: number): Promise<ApiResponse<ProcessingStatus>> {
    const response = await this.client.post<ProcessingStatus>(`/documents/${documentId}/process`);
    return { data: response.data, status: response.status };
  }

  async getDocument(documentId: number): Promise<ApiResponse<Document>> {
    const response = await this.client.get<Document>(`/documents/${documentId}`);
    return { data: response.data, status: response.status };
  }

  async listDocuments(params?: { skip?: number; limit?: number; status?: string }): Promise<ApiResponse<Document[]>> {
    const response = await this.client.get<Document[]>('/documents', { params });
    return { data: response.data, status: response.status };
  }

  // Index Management
  async searchIndex(query: string, limit: number = 10): Promise<ApiResponse<IndexSearchResult[]>> {
    const response = await this.client.get<IndexSearchResult[]>('/index/search', {
      params: { query, limit },
    });
    return { data: response.data, status: response.status };
  }

  async getIndexStats(): Promise<ApiResponse<any>> {
    const response = await this.client.get('/index/stats');
    return { data: response.data, status: response.status };
  }

  // Query Management
  async executeQuery(request: QueryRequest): Promise<ApiResponse<QueryResponse>> {
    const response = await this.client.post<QueryResponse>('/query/execute', request);
    return { data: response.data, status: response.status };
  }

  async getQuerySuggestions(prefix: string): Promise<ApiResponse<string[]>> {
    const response = await this.client.get<string[]>('/query/suggest', {
      params: { prefix },
    });
    return { data: response.data, status: response.status };
  }

  // RAG
  async generateResponse(request: RAGRequest): Promise<ApiResponse<RAGResponse>> {
    const response = await this.client.post<RAGResponse>('/rag/generate', request);
    return { data: response.data, status: response.status };
  }

  async streamResponse(request: RAGRequest): Promise<ReadableStream> {
    const response = await this.client.post('/rag/stream', request, {
      responseType: 'stream',
    });
    return response.data;
  }

  // Search
  async search(request: SearchRequest): Promise<ApiResponse<SearchResponse>> {
    const response = await this.client.post<SearchResponse>('/search', request);
    return { data: response.data, status: response.status };
  }

  async quickSearch(query: string, limit: number = 10): Promise<ApiResponse<SearchResponse>> {
    const response = await this.client.get<SearchResponse>('/search/quick', {
      params: { q: query, limit },
    });
    return { data: response.data, status: response.status };
  }

  // Processing
  async getProcessingStatus(taskId: string): Promise<ApiResponse<ProcessingStatus>> {
    const response = await this.client.get<ProcessingStatus>(`/processing/status/${taskId}`);
    return { data: response.data, status: response.status };
  }

  async retryProcessing(taskId: string): Promise<ApiResponse<ProcessingStatus>> {
    const response = await this.client.post<ProcessingStatus>(`/processing/retry/${taskId}`);
    return { data: response.data, status: response.status };
  }
}

// Create a singleton instance
export const apiClient = new ApiClient();
export default apiClient;
