import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadFile } from '@/lib/utils/upload';
import Button from '../common/Button';
import ProgressBar from '../common/ProgressBar';
import { storageAPI } from '@/lib/api/storage';

interface FileUploaderProps {
  bucket: string;
  onUploadComplete?: () => void;
  onUploadError?: (error: Error) => void;
}

interface UploadingFile {
  id: string;
  file: File;
  progress: number;
  status: 'uploading' | 'completed' | 'error';
  error?: string;
}

const FileUploader: React.FC<FileUploaderProps> = ({
  bucket,
  onUploadComplete,
  onUploadError,
}) => {
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);

  const handleUpload = async (file: File) => {
    const fileId = Math.random().toString(36).substring(7);
    const uploadingFile: UploadingFile = {
      id: fileId,
      file,
      progress: 0,
      status: 'uploading',
    };

    setUploadingFiles((prev) => [...prev, uploadingFile]);

    try {
      const key = `${Date.now()}-${file.name}`;
      const { uploader } = await uploadFile(file, {
        bucket,
        key,
        onProgress: (progress) => {
          setUploadingFiles((prev) =>
            prev.map((f) =>
              f.id === fileId
                ? { ...f, progress: progress.percentage }
                : f
            )
          );
        },
        onComplete: () => {
          setUploadingFiles((prev) =>
            prev.map((f) =>
              f.id === fileId
                ? { ...f, status: 'completed', progress: 100 }
                : f
            )
          );
          onUploadComplete?.();
        },
        onError: (error) => {
          setUploadingFiles((prev) =>
            prev.map((f) =>
              f.id === fileId
                ? { ...f, status: 'error', error: error.message }
                : f
            )
          );
          onUploadError?.(error);
        },
      });
    } catch (error) {
      setUploadingFiles((prev) =>
        prev.map((f) =>
          f.id === fileId
            ? { ...f, status: 'error', error: (error as Error).message }
            : f
        )
      );
      onUploadError?.(error as Error);
    }
  };

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      acceptedFiles.forEach(handleUpload);
    },
    [bucket]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
  });

  const clearCompleted = () => {
    setUploadingFiles((prev) =>
      prev.filter((f) => f.status !== 'completed')
    );
  };

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input {...getInputProps()} />
        <div className="space-y-2">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M24 14v14m7-7l-7 7-7-7m15 15H16a4 4 0 01-4-4V16a4 4 0 014-4h16a4 4 0 014 4v16a4 4 0 01-4 4z"
            />
          </svg>
          <p className="text-gray-600">
            {isDragActive
              ? 'Drop the files here...'
              : 'Drag and drop files here, or click to select files'}
          </p>
        </div>
      </div>

      {uploadingFiles.length > 0 && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium">Uploads</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearCompleted}
              disabled={!uploadingFiles.some((f) => f.status === 'completed')}
            >
              Clear completed
            </Button>
          </div>

          <div className="space-y-3">
            {uploadingFiles.map((file) => (
              <div
                key={file.id}
                className="bg-white rounded-lg border border-gray-200 p-4"
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="truncate">
                    <p className="font-medium truncate">{file.file.name}</p>
                    <p className="text-sm text-gray-500">
                      {(file.file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  <span
                    className={clsx(
                      'px-2 py-1 text-xs rounded-full',
                      file.status === 'uploading' && 'bg-blue-100 text-blue-800',
                      file.status === 'completed' && 'bg-green-100 text-green-800',
                      file.status === 'error' && 'bg-red-100 text-red-800'
                    )}
                  >
                    {file.status === 'uploading' && 'Uploading'}
                    {file.status === 'completed' && 'Completed'}
                    {file.status === 'error' && 'Error'}
                  </span>
                </div>

                {file.status === 'uploading' && (
                  <ProgressBar
                    progress={file.progress}
                    size="sm"
                    color={file.status === 'error' ? 'red' : 'blue'}
                  />
                )}

                {file.status === 'error' && (
                  <p className="text-sm text-red-600 mt-2">{file.error}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUploader;
