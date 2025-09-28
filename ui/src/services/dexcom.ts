import axios, { AxiosError } from 'axios';
import { DexcomStatus, DexcomAuthResponse, DexcomCallbackResponse, ApiError } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001';

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return { Authorization: `Bearer ${token}` };
};

const handleApiError = (error: unknown): never => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiError>;
    throw axiosError.response?.data || { message: axiosError.message };
  }
  throw { message: 'An unexpected error occurred' };
};

const dexcomService = {
  getAuthUrl: async (): Promise<string> => {
    try {
      const response = await axios.get<DexcomAuthResponse>(`${API_BASE_URL}/dexcom/auth-url`, {
        headers: getAuthHeaders()
      });

      return response.data.authUrl;
    } catch (error) {
      return handleApiError(error);
    }
  },

  handleCallback: async (code: string): Promise<DexcomCallbackResponse> => {
    try {
      const response = await axios.post<DexcomCallbackResponse>(`${API_BASE_URL}/dexcom/callback`,
        { code },
        { headers: getAuthHeaders() }
      );

      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  getConnectionStatus: async (): Promise<DexcomStatus> => {
    try {
      const response = await axios.get<DexcomStatus>(`${API_BASE_URL}/dexcom/status`, {
        headers: getAuthHeaders()
      });

      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  disconnectDexcom: async (): Promise<DexcomCallbackResponse> => {
    try {
      const response = await axios.delete<DexcomCallbackResponse>(`${API_BASE_URL}/dexcom/disconnect`, {
        headers: getAuthHeaders()
      });

      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  }
};

export default dexcomService;