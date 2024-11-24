import React from 'react';
import { useStorageAnalytics } from '@/hooks/useStorageAnalytics';

interface StorageAnalyticsProps {}

const StorageAnalytics: React.FC<StorageAnalyticsProps> = () => {
  const { analytics, isLoading, error } = useStorageAnalytics();

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-red-600">Failed to load storage analytics</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-500">Loading analytics...</p>
      </div>
    );
  }

  if (!analytics) {
    return null;
  }

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

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">Storage Analytics</h2>

      <div className="space-y-6">
        {/* Total Storage */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">Total Storage Used</h3>
          <p className="text-2xl font-bold text-gray-900">{formatSize(analytics.totalSize)}</p>
        </div>

        {/* File Count */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">Total Files</h3>
          <p className="text-2xl font-bold text-gray-900">{analytics.totalFiles}</p>
        </div>

        {/* Storage Saved */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">Storage Saved</h3>
          <div className="flex items-baseline space-x-2">
            <p className="text-2xl font-bold text-green-600">
              {formatSize(analytics.savedSpace)}
            </p>
            <p className="text-sm text-gray-500">through deduplication</p>
          </div>
        </div>

        {/* Duplicate Files */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">Duplicate Files</h3>
          <p className="text-2xl font-bold text-gray-900">{analytics.duplicateFiles}</p>
        </div>

        {/* File Type Distribution */}
        {analytics.fileTypes && analytics.fileTypes.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-4">File Type Distribution</h3>
            <div className="space-y-2">
              {analytics.fileTypes.map((type) => (
                <div key={type.extension} className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">{type.extension}</span>
                  <span className="text-sm font-medium text-gray-900">{type.count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StorageAnalytics;
