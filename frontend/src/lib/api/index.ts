import api from '../api';

export interface IndexConfig {
  num_shards: number;
  num_replicas: number;
  refresh_interval_seconds: number;
  compression: 'none' | 'lz4' | 'zstd';
  merge_policy: Record<string, any>;
}

export interface ShardMetrics {
  doc_count: number;
  size_bytes: number;
  memory_bytes: number;
  cpu_percent: number;
  query_latency_ms: number;
  index_latency_ms: number;
}

export interface ShardInfo {
  shard_id: string;
  status: 'active' | 'inactive' | 'recovering' | 'failed';
  node_id: string;
  is_primary: boolean;
  replica_count: number;
  metrics: ShardMetrics;
  last_updated: string;
}

export interface IndexMetrics {
  total_docs: number;
  total_size_bytes: number;
  total_memory_bytes: number;
  avg_cpu_percent: number;
  avg_query_latency_ms: number;
  avg_index_latency_ms: number;
  queries_per_second: number;
  indexing_rate: number;
}

export interface IndexHealth {
  status: 'healthy' | 'degraded' | 'failing';
  message: string;
  issues: string[];
  warnings: string[];
  last_check: string;
}

export interface IndexInfo {
  index_name: string;
  created_at: string;
  updated_at: string;
  config: IndexConfig;
  metrics: IndexMetrics;
  health: IndexHealth;
  shards: Record<string, ShardInfo>;
}

export interface IndexUpdateRequest {
  num_replicas?: number;
  refresh_interval?: number;
  compression?: 'none' | 'lz4' | 'zstd';
  merge_policy?: Record<string, any>;
}

export interface BackupRequest {
  index_name: string;
  backup_name: string;
  include_metrics?: boolean;
}

export interface RestoreRequest {
  backup_name: string;
  target_index?: string;
  restore_metrics?: boolean;
}

export interface BackupInfo {
  backup_name: string;
  index_name: string;
  created_at: string;
  size_bytes: number;
  status: 'completed' | 'failed';
  error?: string;
}

export const indexAPI = {
  /**
   * Create a new index
   */
  createIndex: async (name: string, config: IndexConfig): Promise<IndexInfo> => {
    const response = await api.post('/api/v1/indices', {
      name,
      config,
    });
    return response.data;
  },

  /**
   * Get index information
   */
  getIndex: async (name: string): Promise<IndexInfo> => {
    const response = await api.get(`/api/v1/indices/${name}`);
    return response.data;
  },

  /**
   * Update index configuration
   */
  updateIndex: async (name: string, update: IndexUpdateRequest): Promise<IndexInfo> => {
    const response = await api.patch(`/api/v1/indices/${name}`, update);
    return response.data;
  },

  /**
   * Delete an index
   */
  deleteIndex: async (name: string): Promise<void> => {
    await api.delete(`/api/v1/indices/${name}`);
  },

  /**
   * Create index backup
   */
  createBackup: async (request: BackupRequest): Promise<BackupInfo> => {
    const response = await api.post('/api/v1/indices/backup', request);
    return response.data;
  },

  /**
   * Restore index from backup
   */
  restoreBackup: async (request: RestoreRequest): Promise<IndexInfo> => {
    const response = await api.post('/api/v1/indices/restore', request);
    return response.data;
  },
};
