import { storageAPI } from '../api/storage';
import type { ObjectMetadata, StorageObject } from '../api/storage';

const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB chunk size

export interface UploadProgress {
  uploaded: number;
  total: number;
  percentage: number;
  speed: number; // bytes per second
  remainingTime: number; // seconds
}

export interface UploadOptions {
  bucket: string;
  key: string;
  metadata?: ObjectMetadata;
  onProgress?: (progress: UploadProgress) => void;
  onComplete?: (object: StorageObject) => void;
  onError?: (error: Error) => void;
  chunkSize?: number;
}

export class FileUploader {
  private file: File;
  private options: UploadOptions;
  private abortController: AbortController;
  private startTime: number;
  private uploadedChunks: number;
  private totalChunks: number;
  private uploadId?: string;
  private parts: { part_number: number; etag: string }[];

  constructor(file: File, options: UploadOptions) {
    this.file = file;
    this.options = {
      chunkSize: CHUNK_SIZE,
      ...options,
    };
    this.abortController = new AbortController();
    this.startTime = 0;
    this.uploadedChunks = 0;
    this.totalChunks = Math.ceil(file.size / (this.options.chunkSize || CHUNK_SIZE));
    this.parts = [];
  }

  async start(): Promise<StorageObject> {
    try {
      this.startTime = Date.now();

      if (this.file.size <= (this.options.chunkSize || CHUNK_SIZE)) {
        return this.uploadSinglePart();
      } else {
        return this.uploadMultipart();
      }
    } catch (error) {
      this.options.onError?.(error as Error);
      throw error;
    }
  }

  abort(): void {
    this.abortController.abort();
    if (this.uploadId) {
      storageAPI.abortMultipartUpload(this.options.bucket, this.options.key, this.uploadId)
        .catch(console.error);
    }
  }

  private async uploadSinglePart(): Promise<StorageObject> {
    const { url, fields } = await this.getUploadUrl();
    const formData = new FormData();
    Object.entries(fields).forEach(([key, value]) => {
      formData.append(key, value);
    });
    formData.append('file', this.file);

    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      signal: this.abortController.signal,
    });

    if (!response.ok) {
      throw new Error('Upload failed');
    }

    const object = await storageAPI.getObjectMetadata(
      this.options.bucket,
      this.options.key
    );
    this.options.onComplete?.(object);
    return object;
  }

  private async uploadMultipart(): Promise<StorageObject> {
    const { upload_id, parts } = await storageAPI.createMultipartUpload(
      this.options.bucket,
      this.options.key,
      this.options.metadata
    );
    this.uploadId = upload_id;

    const chunkSize = this.options.chunkSize || CHUNK_SIZE;
    const chunks: Blob[] = [];
    let offset = 0;

    while (offset < this.file.size) {
      chunks.push(this.file.slice(offset, offset + chunkSize));
      offset += chunkSize;
    }

    const uploadPromises = chunks.map((chunk, index) =>
      this.uploadPart(parts[index].url, chunk, index + 1)
    );

    await Promise.all(uploadPromises);

    const object = await storageAPI.completeMultipartUpload(
      this.options.bucket,
      this.options.key,
      this.uploadId,
      this.parts
    );

    this.options.onComplete?.(object);
    return object;
  }

  private async uploadPart(url: string, chunk: Blob, partNumber: number): Promise<void> {
    const response = await fetch(url, {
      method: 'PUT',
      body: chunk,
      signal: this.abortController.signal,
    });

    if (!response.ok) {
      throw new Error(`Failed to upload part ${partNumber}`);
    }

    const etag = response.headers.get('etag');
    if (!etag) {
      throw new Error(`No etag received for part ${partNumber}`);
    }

    this.parts.push({ part_number: partNumber, etag: etag.replace(/['"]/g, '') });
    this.uploadedChunks++;

    this.updateProgress(chunk.size);
  }

  private async getUploadUrl() {
    const config = await storageAPI.getUploadConfig(
      this.options.bucket,
      this.options.key,
      this.options.metadata
    );
    return {
      url: config.presigned_url,
      fields: config.fields,
    };
  }

  private updateProgress(chunkSize: number): void {
    if (!this.options.onProgress) return;

    const uploaded = this.uploadedChunks * (this.options.chunkSize || CHUNK_SIZE);
    const elapsedTime = (Date.now() - this.startTime) / 1000;
    const speed = uploaded / elapsedTime;
    const remainingSize = this.file.size - uploaded;
    const remainingTime = remainingSize / speed;

    this.options.onProgress({
      uploaded,
      total: this.file.size,
      percentage: (uploaded / this.file.size) * 100,
      speed,
      remainingTime,
    });
  }
}

export const uploadFile = async (
  file: File,
  options: UploadOptions
): Promise<{ uploader: FileUploader; promise: Promise<StorageObject> }> => {
  const uploader = new FileUploader(file, options);
  const promise = uploader.start();
  return { uploader, promise };
};
