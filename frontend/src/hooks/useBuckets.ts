import { useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import api from '@/lib/api-client';

export function useBuckets() {
  const queryClient = useQueryClient();

  const {
    data: buckets = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['buckets'],
    queryFn: api.listBuckets,
    onError: (error: Error) => {
      toast.error(`Failed to load buckets: ${error.message}`);
    },
  });

  const createMutation = useMutation({
    mutationFn: api.createBucket,
    onSuccess: (_, name) => {
      queryClient.invalidateQueries({ queryKey: ['buckets'] });
      toast.success(`Bucket "${name}" created successfully`);
    },
    onError: (error: Error, name) => {
      toast.error(`Failed to create bucket "${name}": ${error.message}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: api.deleteBucket,
    onSuccess: (_, name) => {
      queryClient.invalidateQueries({ queryKey: ['buckets'] });
      toast.success(`Bucket "${name}" deleted successfully`);
    },
    onError: (error: Error, name) => {
      toast.error(`Failed to delete bucket "${name}": ${error.message}`);
    },
  });

  const createBucket = useCallback(async (name: string) => {
    await createMutation.mutateAsync(name);
  }, [createMutation]);

  const deleteBucket = useCallback(async (name: string) => {
    await deleteMutation.mutateAsync(name);
  }, [deleteMutation]);

  return {
    buckets,
    isLoading,
    error,
    createBucket,
    deleteBucket,
    isCreating: createMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}
