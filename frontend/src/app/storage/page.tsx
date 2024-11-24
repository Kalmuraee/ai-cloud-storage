'use client';

import React from 'react';
import { useFiles } from '@/hooks/useFiles';
import { useStorageAnalytics } from '@/hooks/useStorageAnalytics';
import FileUploader from '@/components/FileUploader';
import FileList from '@/components/FileList';
import ClientStorageAnalytics from '@/components/features/storage/ClientStorageAnalytics';

export default function StoragePage() {
  const { files, isLoading: filesLoading, error: filesError } = useFiles();
  const { 
    data: analytics, 
    isLoading: analyticsLoading, 
    error: analyticsError 
  } = useStorageAnalytics();

  if (filesError || analyticsError) {
    return (
      <div className="text-red-500">
        Error loading storage data
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Storage</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4">Files</h2>
            <FileUploader />
            {filesLoading ? (
              <div>Loading files...</div>
            ) : (
              <FileList files={files || []} />
            )}
          </div>
        </div>
        
        <div className="lg:col-span-1">
          <ClientStorageAnalytics />
        </div>
      </div>
    </div>
  );
}
