export interface DexcomStatus {
  connected: boolean;
  expires_at?: string | null;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  created_at: string;
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  user: User;
}

export interface RegisterResponse {
  message: string;
}

export interface DexcomAuthResponse {
  authorization_url: string;
  state: string;
}

export interface DexcomCallbackResponse {
  message: string;
}

export interface ApiError {
  detail?: string;
  message?: string;
}

export interface FormData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

export type CallbackStatus = 'processing' | 'success' | 'error';