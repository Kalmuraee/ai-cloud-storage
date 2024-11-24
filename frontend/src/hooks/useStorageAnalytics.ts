import { useQuery } from '@tanstack/react-query';
import { storageService } from '@/services/storage';

interface FileType {
  extension: string;
  count: number;
}

interface StorageAnalytics {
  totalSize: number;
  totalFiles: number;
  savedSpace: number;
  duplicateFiles: number;
  fileTypes: FileType[];
}

export const useStorageAnalytics = () => {
  const { data: analytics, isLoading, error } = useQuery<StorageAnalytics>({
    queryKey: ['storage-analytics'],
    queryFn: () => storageService.getAnalytics(),
  });

  return {
    analytics,
    isLoading,
    error,
  };
};
