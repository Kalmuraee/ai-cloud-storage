import api from '../api';

export interface StorageObject {
  key: string;
  size: number;
  last_modified: string;
  etag: string;
  content_type: string;
  metadata: Record<string, string>;
}

export interface StorageBucket {
  name: string;
  created_at: string;
  object_count: number;
  total_size: number;
  versioning_enabled: boolean;
  lifecycle_rules: BucketLifecycleRule[];
}

export interface BucketLifecycleRule {
  id: string;
  prefix: string;
  enabled: boolean;
  expiration_days?: number;
  transition_days?: number;
  transition_storage_class?: string;
}

export interface UploadConfig {
  presigned_url: string;
  fields: Record<string, string>;
  expires_in: number;
}

export interface ObjectMetadata {
  content_type?: string;
  custom_metadata?: Record<string, string>;
  cache_control?: string;
  content_disposition?: string;
  content_encoding?: string;
  content_language?: string;
  website_redirect_location?: string;
}

export interface ListObjectsOptions {
  prefix?: string;
  delimiter?: string;
  max_keys?: number;
  start_after?: string;
  continuation_token?: string;
}

export interface ListObjectsResponse {
  objects: StorageObject[];
  prefixes: string[];
  is_truncated: boolean;
  next_continuation_token?: string;
}

// Add new interfaces for batch operations
export interface BatchOperation {
  operation: 'delete' | 'copy' | 'move';
  source: {
    bucket: string;
    key: string;
    version_id?: string;
  };
  destination?: {
    bucket: string;
    key: string;
  };
}

export interface BatchOperationResult {
  operation: BatchOperation;
  success: boolean;
  error?: string;
}

// Add new interfaces for storage analytics
export interface StorageAnalytics {
  total_size: number;
  object_count: number;
  bucket_count: number;
  storage_class_distribution: Record<string, number>;
  daily_usage: {
    date: string;
    size: number;
    operations: {
      uploads: number;
      downloads: number;
      deletes: number;
    };
  }[];
}

export const storageAPI = {
  /**
   * List all buckets
   */
  listBuckets: async (): Promise<StorageBucket[]> => {
    const response = await api.get('/api/v1/storage/buckets');
    return response.data;
  },

  /**
   * Create a new bucket
   */
  createBucket: async (name: string, options?: { versioning?: boolean }): Promise<StorageBucket> => {
    const response = await api.post('/api/v1/storage/buckets', { name, ...options });
    return response.data;
  },

  /**
   * Delete a bucket
   */
  deleteBucket: async (name: string, force: boolean = false): Promise<void> => {
    await api.delete(`/api/v1/storage/buckets/${name}`, {
      params: { force }
    });
  },

  /**
   * List objects in a bucket
   */
  listObjects: async (bucketName: string, options?: ListObjectsOptions): Promise<ListObjectsResponse> => {
    const response = await api.get(`/api/v1/storage/buckets/${bucketName}/objects`, {
      params: options
    });
    return response.data;
  },

  /**
   * Get upload configuration
   */
  getUploadConfig: async (
    bucketName: string,
    key: string,
    metadata?: ObjectMetadata
  ): Promise<UploadConfig> => {
    const response = await api.post(`/api/v1/storage/buckets/${bucketName}/upload`, {
      key,
      metadata
    });
    return response.data;
  },

  /**
   * Delete an object
   */
  deleteObject: async (bucketName: string, key: string, versionId?: string): Promise<void> => {
    await api.delete(`/api/v1/storage/buckets/${bucketName}/objects/${key}`, {
      params: { version_id: versionId }
    });
  },

  /**
   * Get object metadata
   */
  getObjectMetadata: async (bucketName: string, key: string, versionId?: string): Promise<StorageObject> => {
    const response = await api.head(`/api/v1/storage/buckets/${bucketName}/objects/${key}`, {
      params: { version_id: versionId }
    });
    return response.data;
  },

  /**
   * Update object metadata
   */
  updateObjectMetadata: async (
    bucketName: string,
    key: string,
    metadata: ObjectMetadata,
    versionId?: string
  ): Promise<StorageObject> => {
    const response = await api.patch(
      `/api/v1/storage/buckets/${bucketName}/objects/${key}/metadata`,
      metadata,
      {
        params: { version_id: versionId }
      }
    );
    return response.data;
  },

  /**
   * Get a presigned URL for downloading an object
   */
  getDownloadUrl: async (
    bucketName: string,
    key: string,
    expiresIn: number = 3600,
    versionId?: string
  ): Promise<string> => {
    const response = await api.get(`/api/v1/storage/buckets/${bucketName}/objects/${key}/download`, {
      params: { expires_in: expiresIn, version_id: versionId }
    });
    return response.data.url;
  },

  // Add batch operations
  async batchOperations(operations: BatchOperation[]): Promise<BatchOperationResult[]> {
    const response = await api.post('/storage/batch', { operations });
    return response.data;
  },

  // Add copy operation
  async copyObject(
    sourceBucket: string,
    sourceKey: string,
    destinationBucket: string,
    destinationKey: string,
    metadata?: ObjectMetadata
  ): Promise<StorageObject> {
    const response = await api.post('/storage/copy', {
      source_bucket: sourceBucket,
      source_key: sourceKey,
      destination_bucket: destinationBucket,
      destination_key: destinationKey,
      metadata,
    });
    return response.data;
  },

  // Add move operation
  async moveObject(
    sourceBucket: string,
    sourceKey: string,
    destinationBucket: string,
    destinationKey: string,
    metadata?: ObjectMetadata
  ): Promise<StorageObject> {
    const response = await api.post('/storage/move', {
      source_bucket: sourceBucket,
      source_key: sourceKey,
      destination_bucket: destinationBucket,
      destination_key: destinationKey,
      metadata,
    });
    return response.data;
  },

  // Add storage analytics
  async getStorageAnalytics(bucketName?: string): Promise<StorageAnalytics> {
    const response = await api.get('/storage/analytics', {
      params: bucketName ? { bucket: bucketName } : undefined,
    });
    return response.data;
  },

  // Add bucket policy management
  async getBucketPolicy(bucketName: string): Promise<Record<string, any>> {
    const response = await api.get(`/storage/buckets/${bucketName}/policy`);
    return response.data;
  },

  async setBucketPolicy(bucketName: string, policy: Record<string, any>): Promise<void> {
    await api.put(`/storage/buckets/${bucketName}/policy`, policy);
  },

  // Add bucket lifecycle management
  async setBucketLifecycle(bucketName: string, rules: BucketLifecycleRule[]): Promise<void> {
    await api.put(`/storage/buckets/${bucketName}/lifecycle`, { rules });
  },

  // Add object tagging
  async getObjectTags(bucketName: string, key: string): Promise<Record<string, string>> {
    const response = await api.get(`/storage/buckets/${bucketName}/objects/${key}/tags`);
    return response.data;
  },

  async setObjectTags(
    bucketName: string,
    key: string,
    tags: Record<string, string>
  ): Promise<void> {
    await api.put(`/storage/buckets/${bucketName}/objects/${key}/tags`, { tags });
  },

  // Add multipart upload helpers
  async createMultipartUpload(
    bucketName: string,
    key: string,
    metadata?: ObjectMetadata
  ): Promise<{ upload_id: string; parts: { url: string; part_number: number }[] }> {
    const response = await api.post('/storage/multipart/create', {
      bucket: bucketName,
      key,
      metadata,
    });
    return response.data;
  },

  async completeMultipartUpload(
    bucketName: string,
    key: string,
    uploadId: string,
    parts: { part_number: number; etag: string }[]
  ): Promise<StorageObject> {
    const response = await api.post('/storage/multipart/complete', {
      bucket: bucketName,
      key,
      upload_id: uploadId,
      parts,
    });
    return response.data;
  },

  async abortMultipartUpload(
    bucketName: string,
    key: string,
    uploadId: string
  ): Promise<void> {
    await api.post('/storage/multipart/abort', {
      bucket: bucketName,
      key,
      upload_id: uploadId,
    });
  },
};
