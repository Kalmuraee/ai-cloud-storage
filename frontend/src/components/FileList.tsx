import React, { useEffect, useState } from 'react';
import { toast } from 'react-hot-toast';
import { FiDownload, FiTrash2, FiCopy, FiShare2 } from 'react-icons/fi';
import { storageApi } from '@/services/storage';
import type { FileMetadata, DuplicateFile } from '@/services/storage';
import { Button } from './common/Button';

interface FileListProps {
  folderId?: number;
  onFileDeleted?: () => void;
}

const FileList: React.FC<FileListProps> = ({ folderId, onFileDeleted }) => {
  const [files, setFiles] = useState<FileMetadata[]>([]);
  const [duplicates, setDuplicates] = useState<DuplicateFile[]>([]);
  const [loading, setLoading] = useState(true);

  const loadFiles = async () => {
    try {
      const [filesData, duplicatesData] = await Promise.all([
        storageApi.listFiles(),
        storageApi.getDuplicates(),
      ]);
      setFiles(filesData);
      setDuplicates(duplicatesData);
    } catch (error: any) {
      console.error('Error loading files:', error);
      toast.error(error.response?.data?.detail || 'Failed to load files');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
  }, [folderId]);

  const handleDownload = async (file: FileMetadata) => {
    try {
      const blob = await storageApi.downloadFile(file.path);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error: any) {
      console.error('Download error:', error);
      toast.error(error.response?.data?.detail || 'Failed to download file');
    }
  };

  const handleDelete = async (file: FileMetadata) => {
    if (!confirm('Are you sure you want to delete this file?')) return;

    try {
      await storageApi.deleteFile(file.path);
      toast.success('File deleted successfully');
      onFileDeleted?.();
      await loadFiles();
    } catch (error: any) {
      console.error('Delete error:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete file');
    }
  };

  const handleShare = async (file: FileMetadata) => {
    try {
      await storageApi.shareItem(file.path);
      toast.success('File shared successfully');
    } catch (error: any) {
      console.error('Share error:', error);
      toast.error(error.response?.data?.detail || 'Failed to share file');
    }
  };

  const isDuplicate = (file: FileMetadata) => {
    return duplicates.some((dup) =>
      dup.files.some((f) => f.id === file.id)
    );
  };

  const formatSize = (bytes: number) => {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  if (loading) {
    return <div className="text-center py-8">Loading...</div>;
  }

  if (files.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No files uploaded yet
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
        {files.map((file) => (
          <div
            key={file.id}
            className="p-4 border rounded-lg shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-medium truncate" title={file.filename}>
                {file.filename}
              </h3>
              {isDuplicate(file) && (
                <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                  Duplicate
                </span>
              )}
            </div>
            
            <div className="text-sm text-gray-500 mb-4">
              <p>{formatSize(file.size)}</p>
              <p>{new Date(file.created_at).toLocaleDateString()}</p>
            </div>

            <div className="flex space-x-2">
              <Button
                onClick={() => handleDownload(file)}
                variant="secondary"
                size="sm"
                title="Download"
              >
                <FiDownload className="w-4 h-4" />
              </Button>
              <Button
                onClick={() => handleShare(file)}
                variant="secondary"
                size="sm"
                title="Share"
              >
                <FiShare2 className="w-4 h-4" />
              </Button>
              <Button
                onClick={() => handleDelete(file)}
                variant="danger"
                size="sm"
                title="Delete"
              >
                <FiTrash2 className="w-4 h-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>

      {duplicates.length > 0 && (
        <div className="mt-8">
          <h2 className="text-lg font-medium mb-4">Duplicate Files</h2>
          <div className="space-y-4">
            {duplicates.map((dup) => (
              <div key={dup.content_hash} className="border rounded-lg p-4">
                <h3 className="font-medium mb-2">
                  Files with hash: {dup.content_hash.slice(0, 8)}...
                </h3>
                <div className="space-y-2">
                  {dup.files.map((file) => (
                    <div
                      key={file.id}
                      className="flex justify-between items-center text-sm"
                    >
                      <span className="truncate">{file.filename}</span>
                      <span className="text-gray-500">
                        {formatSize(file.size)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileList;
