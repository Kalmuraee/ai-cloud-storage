import React from 'react';
import { StorageAnalytics as StorageAnalyticsType } from '@/lib/api/storage';
import Card from '../common/Card';

interface StorageAnalyticsProps {
  analytics: StorageAnalyticsType;
  isLoading?: boolean;
}

const StorageAnalytics: React.FC<StorageAnalyticsProps> = ({
  analytics,
  isLoading = false,
}) => {
  const formatSize = (bytes: number): string => {
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="animate-pulse">
            <div className="h-24 bg-gray-100 rounded"></div>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="p-6">
            <h3 className="text-sm font-medium text-gray-500">Total Storage</h3>
            <p className="mt-2 text-3xl font-semibold text-gray-900">
              {formatSize(analytics.total_size)}
            </p>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <h3 className="text-sm font-medium text-gray-500">Objects</h3>
            <p className="mt-2 text-3xl font-semibold text-gray-900">
              {analytics.object_count.toLocaleString()}
            </p>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <h3 className="text-sm font-medium text-gray-500">Buckets</h3>
            <p className="mt-2 text-3xl font-semibold text-gray-900">
              {analytics.bucket_count.toLocaleString()}
            </p>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <h3 className="text-sm font-medium text-gray-500">
              Daily Operations
            </h3>
            <p className="mt-2 text-3xl font-semibold text-gray-900">
              {analytics.daily_usage[0]?.operations.uploads +
                analytics.daily_usage[0]?.operations.downloads +
                analytics.daily_usage[0]?.operations.deletes || 0}
            </p>
          </div>
        </Card>
      </div>

      <Card>
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Storage Class Distribution
          </h3>
          <div className="space-y-4">
            {Object.entries(analytics.storage_class_distribution).map(
              ([className, size]) => (
                <div key={className}>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-medium text-gray-500">
                      {className}
                    </span>
                    <span className="text-sm text-gray-900">
                      {formatSize(size)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{
                        width: `${(size / analytics.total_size) * 100}%`,
                      }}
                    ></div>
                  </div>
                </div>
              )
            )}
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Daily Usage Trend
          </h3>
          <div className="space-y-6">
            {analytics.daily_usage.slice(0, 7).map((day) => (
              <div key={day.date}>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-500">
                    {new Date(day.date).toLocaleDateString()}
                  </span>
                  <span className="text-sm text-gray-900">
                    {formatSize(day.size)}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Uploads</div>
                    <div className="text-sm font-medium text-gray-900">
                      {day.operations.uploads}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Downloads</div>
                    <div className="text-sm font-medium text-gray-900">
                      {day.operations.downloads}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Deletes</div>
                    <div className="text-sm font-medium text-gray-900">
                      {day.operations.deletes}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  );
};

export default StorageAnalytics;
