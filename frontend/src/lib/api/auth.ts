import api from '../api';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  name: string;
  organization?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserProfile;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  organization?: string;
  role: string;
  created_at: string;
  last_login: string;
  permissions: string[];
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  new_password: string;
}

export interface TokenRefreshRequest {
  refresh_token: string;
}

export const authAPI = {
  /**
   * Login with email and password
   */
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await api.post('/api/v1/auth/login', credentials);
    return response.data;
  },

  /**
   * Register new user
   */
  register: async (data: RegisterData): Promise<AuthResponse> => {
    const response = await api.post('/api/v1/auth/register', data);
    return response.data;
  },

  /**
   * Get current user profile
   */
  getProfile: async (): Promise<UserProfile> => {
    const response = await api.get('/api/v1/auth/profile');
    return response.data;
  },

  /**
   * Update user profile
   */
  updateProfile: async (data: Partial<UserProfile>): Promise<UserProfile> => {
    const response = await api.patch('/api/v1/auth/profile', data);
    return response.data;
  },

  /**
   * Request password reset
   */
  requestPasswordReset: async (data: PasswordResetRequest): Promise<{ message: string }> => {
    const response = await api.post('/api/v1/auth/password-reset', data);
    return response.data;
  },

  /**
   * Confirm password reset
   */
  confirmPasswordReset: async (data: PasswordResetConfirm): Promise<{ message: string }> => {
    const response = await api.post('/api/v1/auth/password-reset/confirm', data);
    return response.data;
  },

  /**
   * Refresh access token
   */
  refreshToken: async (data: TokenRefreshRequest): Promise<AuthResponse> => {
    const response = await api.post('/api/v1/auth/refresh', data);
    return response.data;
  },

  /**
   * Logout user
   */
  logout: async (): Promise<void> => {
    await api.post('/api/v1/auth/logout');
  },
};
