'use client';

import { useState } from 'react';
import { useBuckets } from '@/hooks/useBuckets';
import Button from '@/components/common/Button';
import Card from '@/components/common/Card';

export default function BucketsPage() {
  const [newBucketName, setNewBucketName] = useState('');
  const { buckets, isLoading, createBucket, deleteBucket, isCreating, isDeleting } = useBuckets();

  const handleCreateBucket = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newBucketName.trim()) return;

    try {
      await createBucket(newBucketName);
      setNewBucketName('');
    } catch (error) {
      console.error('Failed to create bucket:', error);
      // Handle error (show toast, etc.)
    }
  };

  const handleDeleteBucket = async (bucketName: string) => {
    if (!confirm(`Are you sure you want to delete the bucket "${bucketName}"?`)) {
      return;
    }

    try {
      await deleteBucket(bucketName);
    } catch (error) {
      console.error('Failed to delete bucket:', error);
      // Handle error (show toast, etc.)
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <Card className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Create New Bucket</h2>
        <form onSubmit={handleCreateBucket} className="flex gap-4">
          <input
            type="text"
            value={newBucketName}
            onChange={(e) => setNewBucketName(e.target.value)}
            placeholder="Enter bucket name"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isCreating}
          />
          <Button type="submit" disabled={isCreating || !newBucketName.trim()}>
            {isCreating ? 'Creating...' : 'Create Bucket'}
          </Button>
        </form>
      </Card>

      <Card>
        <h2 className="text-2xl font-bold mb-4">Storage Buckets</h2>
        {isLoading ? (
          <div className="text-center py-8">Loading buckets...</div>
        ) : buckets.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No buckets found</div>
        ) : (
          <div className="grid gap-4">
            {buckets.map((bucket) => (
              <div
                key={bucket}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
              >
                <div>
                  <h3 className="font-medium">{bucket}</h3>
                </div>
                <Button
                  variant="danger"
                  onClick={() => handleDeleteBucket(bucket)}
                  disabled={isDeleting}
                >
                  Delete
                </Button>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
