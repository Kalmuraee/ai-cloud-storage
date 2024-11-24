import api from '../api';

export interface QueryIntent {
  type: string;
  confidence: number;
  parameters: Record<string, any>;
}

export interface QuerySuggestion {
  text: string;
  score: number;
  type: 'completion' | 'related' | 'popular';
}

export interface QueryCorrection {
  original: string;
  corrected: string;
  confidence: number;
}

export interface QueryExpansion {
  original_query: string;
  expanded_query: string;
  added_terms: string[];
  expansion_type: 'synonym' | 'contextual' | 'domain';
}

export interface ProcessedQuery {
  original_query: string;
  normalized_query: string;
  intent: QueryIntent;
  suggestions: QuerySuggestion[];
  corrections: QueryCorrection[];
  expansions: QueryExpansion[];
  metadata: {
    processing_time: number;
    confidence_score: number;
  };
}

export const queryAPI = {
  /**
   * Process a query with understanding features
   */
  processQuery: async (query: string): Promise<ProcessedQuery> => {
    const response = await api.post('/api/v1/query/process', { query });
    return response.data;
  },

  /**
   * Check query spelling
   */
  checkSpelling: async (query: string): Promise<QueryCorrection[]> => {
    const response = await api.post('/api/v1/query/correct', { query });
    return response.data;
  },
};
