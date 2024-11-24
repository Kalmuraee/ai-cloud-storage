import api from '../api';

export interface UsageMetrics {
  total_requests: number;
  total_documents: number;
  total_storage_bytes: number;
  total_processing_time: number;
  average_response_time: number;
}

export interface TimeseriesPoint {
  timestamp: string;
  value: number;
}

export interface TimeseriesMetrics {
  requests_per_minute: TimeseriesPoint[];
  error_rate: TimeseriesPoint[];
  latency_p95: TimeseriesPoint[];
  storage_usage: TimeseriesPoint[];
}

export interface ErrorMetrics {
  error_count: number;
  error_rate: number;
  top_errors: Array<{
    error_type: string;
    count: number;
    last_occurrence: string;
    sample_message: string;
  }>;
}

export interface CostMetrics {
  total_cost: number;
  cost_by_service: Record<string, number>;
  cost_by_operation: Record<string, number>;
  projected_monthly_cost: number;
}

export interface UserActivityMetrics {
  total_users: number;
  active_users: number;
  new_users: number;
  user_actions: Record<string, number>;
}

export const analyticsAPI = {
  /**
   * Get general usage metrics
   */
  getUsageMetrics: async (start_date?: string, end_date?: string): Promise<UsageMetrics> => {
    const response = await api.get('/api/v1/analytics/usage', {
      params: { start_date, end_date }
    });
    return response.data;
  },

  /**
   * Get timeseries metrics
   */
  getTimeseriesMetrics: async (
    metric_type: string,
    interval: 'minute' | 'hour' | 'day',
    start_date: string,
    end_date: string
  ): Promise<TimeseriesMetrics> => {
    const response = await api.get('/api/v1/analytics/timeseries', {
      params: { metric_type, interval, start_date, end_date }
    });
    return response.data;
  },

  /**
   * Get error metrics
   */
  getErrorMetrics: async (start_date?: string, end_date?: string): Promise<ErrorMetrics> => {
    const response = await api.get('/api/v1/analytics/errors', {
      params: { start_date, end_date }
    });
    return response.data;
  },

  /**
   * Get cost metrics
   */
  getCostMetrics: async (start_date?: string, end_date?: string): Promise<CostMetrics> => {
    const response = await api.get('/api/v1/analytics/costs', {
      params: { start_date, end_date }
    });
    return response.data;
  },

  /**
   * Get user activity metrics
   */
  getUserActivityMetrics: async (start_date?: string, end_date?: string): Promise<UserActivityMetrics> => {
    const response = await api.get('/api/v1/analytics/user-activity', {
      params: { start_date, end_date }
    });
    return response.data;
  },
};
