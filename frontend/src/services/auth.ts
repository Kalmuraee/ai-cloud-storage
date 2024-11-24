import axios from 'axios';
import { API_BASE_URL, API_ENDPOINTS } from '@/config';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  password: string;
}

export interface User {
  id: string;
  email: string;
}

const authApi = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

export const authService = {
  async login({ username, password }: LoginCredentials): Promise<User> {
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await authApi.post(API_ENDPOINTS.AUTH.LOGIN, formData);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(error.response.data.detail || 'Login failed');
      }
      throw new Error('Network error occurred');
    }
  },

  async register({ email, password }: RegisterCredentials): Promise<User> {
    try {
      const response = await authApi.post(API_ENDPOINTS.AUTH.REGISTER, {
        email,
        password,
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(error.response.data.detail || 'Registration failed');
      }
      throw new Error('Network error occurred');
    }
  },

  async logout(): Promise<void> {
    await authApi.post(API_ENDPOINTS.AUTH.LOGOUT);
  },

  async getCurrentUser(): Promise<User | null> {
    try {
      const response = await authApi.get(API_ENDPOINTS.AUTH.ME);
      return response.data;
    } catch (error) {
      return null;
    }
  },
};
