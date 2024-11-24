import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import api, { FileMetadata } from '@/lib/api-client';

export function useFiles(bucket?: string) {
  const queryClient = useQueryClient();
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});

  const {
    data: files = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['files', bucket],
    queryFn: () => api.listFiles(bucket),
    onError: (error: Error) => {
      toast.error(`Failed to load files: ${error.message}`);
    },
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const uploadResponse = await api.getUploadUrl(file.name, file.type);
      await api.uploadFile(uploadResponse.upload_url, file);
      return uploadResponse;
    },
    onSuccess: (_, file) => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
      toast.success(`Successfully uploaded ${file.name}`);
    },
    onError: (error: Error, file) => {
      toast.error(`Failed to upload ${file.name}: ${error.message}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: api.deleteFile,
    onSuccess: (_, fileId) => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
      toast.success('File deleted successfully');
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete file: ${error.message}`);
    },
  });

  const uploadFile = useCallback(async (file: File) => {
    try {
      setUploadProgress((prev) => ({ ...prev, [file.name]: 0 }));
      await uploadMutation.mutateAsync(file);
      setUploadProgress((prev) => ({ ...prev, [file.name]: 100 }));
    } catch (error) {
      setUploadProgress((prev) => {
        const newProgress = { ...prev };
        delete newProgress[file.name];
        return newProgress;
      });
      throw error;
    }
  }, [uploadMutation]);

  const deleteFile = useCallback(async (fileId: string) => {
    await deleteMutation.mutateAsync(fileId);
  }, [deleteMutation]);

  const getDownloadUrl = useCallback(async (fileId: string) => {
    try {
      const url = await api.getDownloadUrl(fileId);
      toast.success('Download started');
      return url;
    } catch (error) {
      toast.error('Failed to get download URL');
      throw error;
    }
  }, []);

  return {
    files,
    isLoading,
    error,
    uploadFile,
    deleteFile,
    getDownloadUrl,
    uploadProgress,
    isUploading: uploadMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}
