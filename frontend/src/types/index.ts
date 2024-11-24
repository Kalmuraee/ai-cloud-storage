export interface FileItem {
  id: string;
  name: string;
  type: string;
  size: number;
  uploadedAt: string;
  url: string;
}

export interface StorageStats {
  total_size: number;
  file_count: number;
  bucket_stats: {
    [bucket: string]: {
      size: number;
      count: number;
    };
  };
  size: number;
  count: number;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

export interface FileUploadResponse {
  file_id: string;
  filename: string;
  size: number;
  content_type: string;
  upload_url: string;
}
