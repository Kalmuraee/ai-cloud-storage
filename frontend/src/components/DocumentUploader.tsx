import React, { useCallback } from 'react';
import { useUploadDocument } from '../hooks/useApi';
import { useDocumentStore } from '../store/store';

export const DocumentUploader: React.FC = () => {
  const { execute: uploadDocument, loading, error } = useUploadDocument();
  const addDocument = useDocumentStore((state) => state.addDocument);

  const handleFileChange = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      try {
        const response = await uploadDocument(file);
        if (response?.data) {
          addDocument(response.data);
        }
      } catch (err) {
        console.error('Error uploading document:', err);
      }
    },
    [uploadDocument, addDocument]
  );

  return (
    <div className="p-4">
      <label className="block">
        <span className="sr-only">Choose file</span>
        <input
          type="file"
          className="block w-full text-sm text-slate-500
            file:mr-4 file:py-2 file:px-4
            file:rounded-full file:border-0
            file:text-sm file:font-semibold
            file:bg-violet-50 file:text-violet-700
            hover:file:bg-violet-100"
          onChange={handleFileChange}
          disabled={loading}
        />
      </label>
      {loading && <p className="mt-2 text-sm text-gray-500">Uploading...</p>}
      {error && <p className="mt-2 text-sm text-red-500">{error.message}</p>}
    </div>
  );
};
