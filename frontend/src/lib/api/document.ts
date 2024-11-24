import api from '../api';

export interface ProcessingRequest {
  bucket_name: string;
  object_name: string;
}

export interface ProcessingStatus {
  status: 'success' | 'error';
  message: string;
}

export interface ProcessedDocument {
  chunks: Array<{
    text: string;
    chunk_type: 'text' | 'code' | 'table';
    metadata: Record<string, any>;
  }>;
  tables: Array<{
    data: any[][];
    headers: string[];
    metadata: Record<string, any>;
  }>;
  images: Array<{
    url: string;
    metadata: Record<string, any>;
  }>;
  metadata: Record<string, any>;
}

export const documentAPI = {
  /**
   * Process a single document
   */
  processDocument: async (file: File, targetLanguage: string = 'en'): Promise<ProcessedDocument> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_language', targetLanguage);

    const response = await api.post('/api/v1/document/process', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Process multiple documents in parallel
   */
  processBatch: async (files: File[], targetLanguage: string = 'en'): Promise<ProcessedDocument[]> => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    formData.append('target_language', targetLanguage);

    const response = await api.post('/api/v1/document/process/batch', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Process a document from storage
   */
  processStoredDocument: async (request: ProcessingRequest): Promise<ProcessingStatus> => {
    const response = await api.post('/api/v1/processing/process', request);
    return response.data;
  },

  /**
   * Delete a processed document
   */
  deleteProcessedDocument: async (bucketName: string, objectName: string): Promise<void> => {
    await api.delete(`/api/v1/processing/${bucketName}/objects/${objectName}`);
  },
};
