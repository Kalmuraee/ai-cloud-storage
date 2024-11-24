import React, { useEffect } from 'react';
import { useListDocuments } from '../hooks/useApi';
import { useDocumentStore } from '../store/store';
import { Document } from '../lib/api/types';

export const DocumentList: React.FC = () => {
  const { execute: fetchDocuments, loading, error } = useListDocuments();
  const { documents, setDocuments, setSelectedDocument } = useDocumentStore();

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const response = await fetchDocuments();
        if (response?.data) {
          setDocuments(response.data);
        }
      } catch (err) {
        console.error('Error fetching documents:', err);
      }
    };

    loadDocuments();
  }, [fetchDocuments, setDocuments]);

  const handleDocumentClick = (document: Document) => {
    setSelectedDocument(document);
  };

  if (loading) {
    return <div className="p-4">Loading documents...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-500">Error: {error.message}</div>;
  }

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold mb-4">Documents</h2>
      <div className="space-y-2">
        {documents.map((doc) => (
          <div
            key={doc.id}
            className="p-3 bg-white rounded-lg shadow hover:shadow-md cursor-pointer transition-shadow"
            onClick={() => handleDocumentClick(doc)}
          >
            <h3 className="font-medium">{doc.title}</h3>
            <div className="text-sm text-gray-500">
              <span>{doc.content_type}</span>
              <span className="mx-2">•</span>
              <span>{formatBytes(doc.size)}</span>
            </div>
          </div>
        ))}
        {documents.length === 0 && (
          <div className="text-center text-gray-500">No documents found</div>
        )}
      </div>
    </div>
  );
};

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}
