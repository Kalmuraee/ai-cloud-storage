import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { toast } from 'react-hot-toast';
import { FiUploadCloud } from 'react-icons/fi';
import { storageApi } from '@/services/storage';
import { Button } from './common/Button';
import { ProgressBar } from './common/ProgressBar';

interface FileUploaderProps {
  onUploadComplete?: () => void;
  folderId?: number;
}

const FileUploader: React.FC<FileUploaderProps> = ({
  onUploadComplete,
  folderId,
}) => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [checkDuplicates, setCheckDuplicates] = useState(true);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    setUploading(true);
    setProgress(0);

    try {
      for (const file of acceptedFiles) {
        setProgress((prev) => prev + (100 / acceptedFiles.length) * 0.1);

        const response = await storageApi.uploadFile(file, folderId, checkDuplicates);

        if (response.is_duplicate) {
          toast.success(`File "${file.name}" already exists and was deduplicated`);
        } else {
          toast.success(`File "${file.name}" uploaded successfully`);
        }

        setProgress((prev) => prev + (100 / acceptedFiles.length) * 0.9);
      }

      onUploadComplete?.();
    } catch (error: any) {
      console.error('Upload error:', error);
      toast.error(error.response?.data?.detail || 'Failed to upload file');
    } finally {
      setUploading(false);
      setProgress(0);
    }
  }, [folderId, checkDuplicates, onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled: uploading,
  });

  return (
    <div className="w-full max-w-xl mx-auto">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-colors duration-200 ease-in-out
          ${isDragActive ? 'border-primary bg-primary/5' : 'border-gray-300'}
          ${uploading ? 'opacity-50 cursor-not-allowed' : 'hover:border-primary hover:bg-primary/5'}
        `}
      >
        <input {...getInputProps()} />
        <FiUploadCloud className="mx-auto h-12 w-12 text-gray-400" />
        <p className="mt-2 text-sm text-gray-600">
          {isDragActive
            ? 'Drop the files here...'
            : 'Drag and drop files here, or click to select files'}
        </p>
      </div>

      <div className="mt-4 space-y-4">
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="checkDuplicates"
            checked={checkDuplicates}
            onChange={(e) => setCheckDuplicates(e.target.checked)}
            className="rounded border-gray-300 text-primary focus:ring-primary"
          />
          <label htmlFor="checkDuplicates" className="text-sm text-gray-600">
            Check for duplicates before upload
          </label>
        </div>

        {uploading && (
          <div className="space-y-2">
            <ProgressBar progress={progress} />
            <p className="text-sm text-gray-500 text-center">
              Uploading... {Math.round(progress)}%
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUploader;
