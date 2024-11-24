import api from '../api';

export interface SearchQuery {
  query: string;
  filters?: Record<string, any>;
  page?: number;
  limit?: number;
  min_score?: number;
}

export interface SearchResult {
  id: string;
  content: string;
  score: number;
  metadata: Record<string, any>;
  highlights: Array<{
    field: string;
    snippet: string;
  }>;
}

export interface SearchFacet {
  field: string;
  value: string;
  count: number;
}

export interface SearchResponse {
  results: SearchResult[];
  facets: Record<string, SearchFacet[]>;
  total: number;
  took: number;
  query_id: string;
}

export interface FeedbackQuery {
  query_id: string;
  result_id: string;
  is_relevant: boolean;
  feedback_type: 'click' | 'like' | 'dislike';
  comments?: string;
}

export const searchAPI = {
  /**
   * Perform semantic search
   */
  search: async (query: SearchQuery): Promise<SearchResponse> => {
    const response = await api.post('/api/v1/search', query);
    return response.data;
  },

  /**
   * Submit search result feedback
   */
  submitFeedback: async (feedback: FeedbackQuery): Promise<void> => {
    await api.post('/api/v1/search/feedback', feedback);
  },
};
