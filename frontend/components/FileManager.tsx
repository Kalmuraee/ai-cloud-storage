import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { 
  FiFolder, 
  FiFile, 
  FiUpload, 
  FiTrash2, 
  FiDownload,
  FiSearch
} from 'react-icons/fi';
import { Dialog, Transition } from '@headlessui/react';

interface File {
  id: string;
  name: string;
  size: number;
  type: string;
  lastModified: string;
  metadata: Record<string, any>;
}

interface Folder {
  id: string;
  name: string;
  files: File[];
  subfolders: Folder[];
}

const FileManager: React.FC = () => {
  const [currentPath, setCurrentPath] = useState<string[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const queryClient = useQueryClient();

  // Fetch files and folders
  const { data: fileStructure, isLoading } = useQuery(
    ['files', currentPath.join('/')],
    async () => {
      const response = await fetch(`/api/storage/list?path=${currentPath.join('/')}`);
      if (!response.ok) throw new Error('Failed to fetch files');
      return response.json();
    }
  );

  // Upload files mutation
  const uploadMutation = useMutation(
    async (files: FileList) => {
      const formData = new FormData();
      Array.from(files).forEach(file => {
        formData.append('files', file);
      });
      formData.append('path', currentPath.join('/'));

      const response = await fetch('/api/storage/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');
      return response.json();
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['files', currentPath.join('/')]);
        setIsUploadModalOpen(false);
      },
    }
  );

  // Delete files mutation
  const deleteMutation = useMutation(
    async (fileIds: string[]) => {
      const response = await fetch('/api/storage/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileIds }),
      });

      if (!response.ok) throw new Error('Delete failed');
      return response.json();
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['files', currentPath.join('/')]);
        setSelectedFiles(new Set());
      },
    }
  );

  // Download file
  const downloadFile = async (fileId: string) => {
    const response = await fetch(`/api/storage/download/${fileId}`);
    if (!response.ok) throw new Error('Download failed');
    
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileId.split('/').pop() || 'download';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  // Handle file selection
  const toggleFileSelection = (fileId: string) => {
    const newSelection = new Set(selectedFiles);
    if (newSelection.has(fileId)) {
      newSelection.delete(fileId);
    } else {
      newSelection.add(fileId);
    }
    setSelectedFiles(newSelection);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setIsUploadModalOpen(true)}
            className="flex items-center px-4 py-2 text-white bg-blue-500 rounded hover:bg-blue-600"
          >
            <FiUpload className="mr-2" />
            Upload
          </button>
          <button
            onClick={() => deleteMutation.mutate(Array.from(selectedFiles))}
            disabled={selectedFiles.size === 0}
            className="flex items-center px-4 py-2 text-white bg-red-500 rounded hover:bg-red-600 disabled:opacity-50"
          >
            <FiTrash2 className="mr-2" />
            Delete
          </button>
        </div>
        
        <div className="flex items-center">
          <div className="relative">
            <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search files..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Breadcrumb */}
      <div className="flex items-center p-4 text-sm text-gray-600">
        <button
          onClick={() => setCurrentPath([])}
          className="hover:text-blue-500"
        >
          Root
        </button>
        {currentPath.map((folder, index) => (
          <React.Fragment key={folder}>
            <span className="mx-2">/</span>
            <button
              onClick={() => setCurrentPath(currentPath.slice(0, index + 1))}
              className="hover:text-blue-500"
            >
              {folder}
            </button>
          </React.Fragment>
        ))}
      </div>

      {/* File List */}
      <div className="flex-1 overflow-auto p-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {fileStructure?.folders?.map((folder: Folder) => (
              <div
                key={folder.id}
                onClick={() => setCurrentPath([...currentPath, folder.name])}
                className="flex items-center p-4 space-x-3 border rounded-lg cursor-pointer hover:bg-gray-50"
              >
                <FiFolder className="text-2xl text-yellow-500" />
                <span className="flex-1 truncate">{folder.name}</span>
              </div>
            ))}
            
            {fileStructure?.files?.map((file: File) => (
              <div
                key={file.id}
                className={`flex items-center p-4 space-x-3 border rounded-lg cursor-pointer hover:bg-gray-50 ${
                  selectedFiles.has(file.id) ? 'bg-blue-50 border-blue-500' : ''
                }`}
                onClick={() => toggleFileSelection(file.id)}
              >
                <FiFile className="text-2xl text-gray-500" />
                <div className="flex-1 min-w-0">
                  <div className="truncate">{file.name}</div>
                  <div className="text-sm text-gray-500">
                    {(file.size / 1024).toFixed(2)} KB
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    downloadFile(file.id);
                  }}
                  className="p-2 hover:bg-gray-100 rounded"
                >
                  <FiDownload />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upload Modal */}
      <Transition show={isUploadModalOpen} as={React.Fragment}>
        <Dialog
          onClose={() => setIsUploadModalOpen(false)}
          className="fixed inset-0 z-10 overflow-y-auto"
        >
          <div className="flex items-center justify-center min-h-screen">
            <Dialog.Overlay className="fixed inset-0 bg-black opacity-30" />

            <div className="relative bg-white rounded-lg p-8 max-w-md w-full mx-4">
              <Dialog.Title className="text-lg font-medium mb-4">
                Upload Files
              </Dialog.Title>

              <input
                type="file"
                multiple
                onChange={(e) => {
                  if (e.target.files) {
                    uploadMutation.mutate(e.target.files);
                  }
                }}
                className="w-full p-2 border rounded"
              />

              <div className="mt-6 flex justify-end space-x-4">
                <button
                  onClick={() => setIsUploadModalOpen(false)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    // Handle upload confirmation if needed
                  }}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  Upload
                </button>
              </div>
            </div>
          </div>
        </Dialog>
      </Transition>
    </div>
  );
};

export default FileManager;
