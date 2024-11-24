import React, { useState } from 'react';
import { format } from 'date-fns';
import { StorageObject } from '@/lib/api/storage';
import Card from '../common/Card';
import Button from '../common/Button';

interface FileListProps {
  files: StorageObject[];
  onDownload: (file: StorageObject) => void;
  onDelete: (file: StorageObject) => void;
  isLoading?: boolean;
}

const FileList: React.FC<FileListProps> = ({
  files,
  onDownload,
  onDelete,
  isLoading = false,
}) => {
  const [selectedFile, setSelectedFile] = useState<StorageObject | null>(null);

  const formatFileSize = (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="animate-pulse">
            <div className="h-16 bg-gray-100 rounded"></div>
          </Card>
        ))}
      </div>
    );
  }

  if (files.length === 0) {
    return (
      <Card className="py-12">
        <div className="text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No files</h3>
          <p className="mt-1 text-sm text-gray-500">
            Upload files to see them here
          </p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {files.map((file) => (
        <Card
          key={file.key}
          className={`cursor-pointer transition-colors ${
            selectedFile?.key === file.key
              ? 'bg-blue-50 border-blue-200'
              : 'hover:bg-gray-50'
          }`}
          onClick={() => setSelectedFile(file)}
        >
          <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  <svg
                    className="h-6 w-6 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                    />
                  </svg>
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {file.key.split('/').pop()}
                  </p>
                  <div className="flex items-center space-x-4">
                    <p className="text-sm text-gray-500">
                      {formatFileSize(file.size)}
                    </p>
                    <p className="text-sm text-gray-500">
                      {format(new Date(file.last_modified), 'MMM d, yyyy')}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div className="ml-4 flex-shrink-0 space-x-2">
              <Button
                size="sm"
                variant="secondary"
                onClick={(e) => {
                  e.stopPropagation();
                  onDownload(file);
                }}
              >
                Download
              </Button>
              <Button
                size="sm"
                variant="danger"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(file);
                }}
              >
                Delete
              </Button>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
};

export default FileList;
