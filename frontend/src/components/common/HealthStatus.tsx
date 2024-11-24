import React from 'react';
import { useHealth } from '../../hooks/useHealth';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/solid';

export const HealthStatus: React.FC = () => {
  const { data: health, isLoading, isError } = useHealth();

  if (isLoading) {
    return (
      <div className="flex items-center text-gray-500">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-500 mr-2" />
        Checking health...
      </div>
    );
  }

  if (isError || !health) {
    return (
      <div className="flex items-center text-red-500">
        <XCircleIcon className="h-5 w-5 mr-2" />
        Service unavailable
      </div>
    );
  }

  const isHealthy = health.status === 'healthy';
  const redisStatus = health.services.redis === 'connected';

  return (
    <div className="flex flex-col space-y-2">
      <div className={`flex items-center ${isHealthy ? 'text-green-500' : 'text-red-500'}`}>
        {isHealthy ? (
          <CheckCircleIcon className="h-5 w-5 mr-2" />
        ) : (
          <XCircleIcon className="h-5 w-5 mr-2" />
        )}
        System Status: {health.status}
      </div>
      
      <div className={`flex items-center text-sm ${redisStatus ? 'text-green-500' : 'text-red-500'}`}>
        {redisStatus ? (
          <CheckCircleIcon className="h-4 w-4 mr-2" />
        ) : (
          <XCircleIcon className="h-4 w-4 mr-2" />
        )}
        Redis: {health.services.redis}
      </div>
    </div>
  );
};
