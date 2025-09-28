import axios, { AxiosError } from 'axios';
import { User, LoginResponse, RegisterResponse, ApiError } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const handleApiError = (error: unknown): never => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiError>;
    throw axiosError.response?.data || { message: axiosError.message };
  }
  throw { message: 'An unexpected error occurred' };
};

const authService = {
  login: async (email: string, password: string): Promise<LoginResponse> => {
    try {
      const response = await axios.post<LoginResponse>(`${API_BASE_URL}/v1/auth/login`, {
        email,
        password
      });

      const { access_token, user } = response.data;
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));

      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  register: async (email: string, password: string, first_name: string, last_name: string): Promise<RegisterResponse> => {
    try {
      const response = await axios.post<RegisterResponse>(`${API_BASE_URL}/v1/auth/register`, {
        email,
        password,
        first_name,
        last_name
      });

      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  logout: async (): Promise<void> => {
    try {
      const token = localStorage.getItem('token');
      if (token) {
        // Attempt to logout on server
        await axios.post(`${API_BASE_URL}/v1/auth/logout`, {}, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
      }
    } catch (error) {
      // Ignore errors during logout - always clear local storage
      console.warn('Error during logout:', error);
    } finally {
      // Always clear local storage regardless of server response
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
  },

  getCurrentUser: (): User | null => {
    const user = localStorage.getItem('user');
    if (!user) {
      return null;
    }
    try {
      return JSON.parse(user);
    } catch (error) {
      console.error('Error parsing user data from localStorage:', error);
      localStorage.removeItem('user');
      return null;
    }
  },

  isAuthenticated: (): boolean => {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    return !!(token && user);
  },

  updateProfile: async (profileData: Partial<{ first_name: string; last_name: string; email: string }>): Promise<User> => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw { message: 'No authentication token found' };
      }

      const response = await axios.put<User>(`${API_BASE_URL}/v1/users/me`, profileData, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      // Update localStorage with new user data
      localStorage.setItem('user', JSON.stringify(response.data));

      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  deactivateAccount: async (): Promise<void> => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw { message: 'No authentication token found' };
      }

      await axios.delete(`${API_BASE_URL}/v1/users/me`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      // Clear local storage after successful deactivation
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    } catch (error) {
      return handleApiError(error);
    }
  },

  confirmEmail: async (email: string, confirmationCode: string): Promise<void> => {
    try {
      await axios.post(`${API_BASE_URL}/v1/auth/confirm-email`, {
        email,
        confirmation_code: confirmationCode
      });
    } catch (error) {
      return handleApiError(error);
    }
  },

  resendConfirmation: async (email: string): Promise<void> => {
    try {
      await axios.post(`${API_BASE_URL}/v1/auth/resend-confirmation`, {
        email
      });
    } catch (error) {
      return handleApiError(error);
    }
  }
};

export default authService;