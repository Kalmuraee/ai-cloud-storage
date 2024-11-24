import api from '../api';

export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  services: {
    redis: 'connected' | 'disconnected';
  };
}

export const healthAPI = {
  /**
   * Check the health status of the backend services
   */
  checkHealth: async (): Promise<HealthStatus> => {
    const response = await api.get('/api/health');
    return response.data;
  },
};
