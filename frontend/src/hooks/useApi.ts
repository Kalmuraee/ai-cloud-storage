import { useState, useCallback } from 'react';
import { ApiResponse, ApiError } from '../lib/api/types';
import apiClient from '../lib/api/client';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
}

interface UseApiResponse<T> extends UseApiState<T> {
  execute: (...args: any[]) => Promise<void>;
  reset: () => void;
}

export function useApi<T>(
  apiMethod: (...args: any[]) => Promise<ApiResponse<T>>,
  options: { immediate?: boolean; onSuccess?: (data: T) => void; onError?: (error: ApiError) => void } = {}
): UseApiResponse<T> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(
    async (...args: any[]) => {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const response = await apiMethod(...args);
        if (response.data) {
          setState({ data: response.data, loading: false, error: null });
          options.onSuccess?.(response.data);
        } else {
          throw new Error('No data received');
        }
      } catch (error: any) {
        const apiError: ApiError = {
          message: error.message || 'An unexpected error occurred',
          code: error.code || 'UNKNOWN_ERROR',
          details: error.details,
        };
        setState((prev) => ({ ...prev, loading: false, error: apiError }));
        options.onError?.(apiError);
      }
    },
    [apiMethod, options]
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
}

// Document hooks
export function useUploadDocument() {
  return useApi(apiClient.uploadDocument.bind(apiClient));
}

export function useProcessDocument() {
  return useApi(apiClient.processDocument.bind(apiClient));
}

export function useGetDocument() {
  return useApi(apiClient.getDocument.bind(apiClient));
}

export function useListDocuments() {
  return useApi(apiClient.listDocuments.bind(apiClient));
}

// Index hooks
export function useSearchIndex() {
  return useApi(apiClient.searchIndex.bind(apiClient));
}

export function useIndexStats() {
  return useApi(apiClient.getIndexStats.bind(apiClient));
}

// Query hooks
export function useExecuteQuery() {
  return useApi(apiClient.executeQuery.bind(apiClient));
}

export function useQuerySuggestions() {
  return useApi(apiClient.getQuerySuggestions.bind(apiClient));
}

// RAG hooks
export function useGenerateResponse() {
  return useApi(apiClient.generateResponse.bind(apiClient));
}

// Search hooks
export function useSearch() {
  return useApi(apiClient.search.bind(apiClient));
}

export function useQuickSearch() {
  return useApi(apiClient.quickSearch.bind(apiClient));
}

// Processing hooks
export function useProcessingStatus() {
  return useApi(apiClient.getProcessingStatus.bind(apiClient));
}

export function useRetryProcessing() {
  return useApi(apiClient.retryProcessing.bind(apiClient));
}
