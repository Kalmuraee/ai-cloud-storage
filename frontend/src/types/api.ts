export interface ApiError {
  status: number;
  message: string;
  details?: Record<string, any>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

export interface FileMetadata {
  size: number;
  last_modified: string;
  etag: string;
  content_type: string;
  metadata?: Record<string, string>;
}

export interface FileUploadResponse {
  message: string;
  file_info: {
    bucket: string;
    path: string;
    etag: string;
    version_id?: string;
    size: number;
    content_type: string;
  };
}

export interface FileListResponse {
  files: {
    name: string;
    size: number;
    last_modified: string;
    etag: string;
    content_type: string;
  }[];
}

export interface PresignedUrlResponse {
  url: string;
  expires_in: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  user: {
    id: string;
    email: string;
    username: string;
    full_name: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
  };
}

export interface UserProfile {
  id: string;
  email: string;
  username: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DocumentMetadata {
  id: string;
  title: string;
  description?: string;
  file_path: string;
  file_type: string;
  file_size: number;
  created_at: string;
  updated_at: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface SearchResult {
  id: string;
  title: string;
  description?: string;
  file_path: string;
  score: number;
  highlights?: {
    field: string;
    snippet: string;
  }[];
  metadata?: Record<string, any>;
}
