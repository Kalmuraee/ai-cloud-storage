import api from '../api';

export interface Document {
  id: string;
  content: string;
  metadata: Record<string, any>;
}

export interface QueryRequest {
  query: string;
  filters?: Record<string, any>;
  top_k?: number;
  threshold?: number;
}

export interface QueryResult {
  answer: string;
  confidence: number;
  sources: Array<{
    document_id: string;
    content: string;
    relevance_score: number;
  }>;
  metadata: {
    processing_time: number;
    model_version: string;
    tokens_used: number;
  };
}

export interface IndexStats {
  total_documents: number;
  total_chunks: number;
  index_size_bytes: number;
  last_updated: string;
  embedding_model: string;
  language_model: string;
}

export const ragAPI = {
  /**
   * Process a document for RAG
   */
  processDocument: async (document: Document, forceUpdate: boolean = false): Promise<{ message: string; doc_id: string }> => {
    const response = await api.post('/api/v1/rag/process', {
      document,
      force_update: forceUpdate,
    });
    return response.data;
  },

  /**
   * Query the RAG system
   */
  query: async (request: QueryRequest): Promise<QueryResult> => {
    const response = await api.post('/api/v1/rag/query', request);
    return response.data;
  },

  /**
   * Get RAG index statistics
   */
  getStats: async (): Promise<IndexStats> => {
    const response = await api.get('/api/v1/rag/stats');
    return response.data;
  },
};
