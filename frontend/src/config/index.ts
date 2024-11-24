// API Configuration
export const API_BASE_URL = '/api';

// Storage Configuration
export const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB
export const ALLOWED_FILE_TYPES = [
  'image/*',
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
  'application/json',
  'application/zip',
  'application/x-zip-compressed',
];

// UI Configuration
export const TOAST_DURATION = 3000;
export const ITEMS_PER_PAGE = 20;

// Feature Flags
export const FEATURES = {
  FILE_DEDUPLICATION: true,
  FILE_SHARING: true,
  FILE_VERSIONING: false,
  ADVANCED_SEARCH: true,
};

// Error Messages
export const ERROR_MESSAGES = {
  FILE_TOO_LARGE: `File size exceeds the maximum limit of ${MAX_FILE_SIZE / (1024 * 1024)}MB`,
  UNSUPPORTED_FILE_TYPE: 'File type not supported',
  UPLOAD_FAILED: 'Failed to upload file',
  DOWNLOAD_FAILED: 'Failed to download file',
  DELETE_FAILED: 'Failed to delete file',
  NETWORK_ERROR: 'Network error occurred',
  UNAUTHORIZED: 'You are not authorized to perform this action',
};

// Success Messages
export const SUCCESS_MESSAGES = {
  FILE_UPLOADED: 'File uploaded successfully',
  FILE_DELETED: 'File deleted successfully',
  FILE_SHARED: 'File shared successfully',
  DUPLICATE_FOUND: 'Duplicate file detected and deduplicated',
};
