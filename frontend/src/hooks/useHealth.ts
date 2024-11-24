import { useQuery } from '@tanstack/react-query';
import { healthAPI, HealthStatus } from '../lib/api/health';

export const useHealth = () => {
  return useQuery<HealthStatus>({
    queryKey: ['health'],
    queryFn: healthAPI.checkHealth,
    refetchInterval: 30000, // Check health every 30 seconds
    retry: 3,
  });
};
