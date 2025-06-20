// src/services/authService.ts
import apiClient from './apiClient';
import { LoginFormInputs } from '../types/authSchemas';
import { Token } from '../types/token';
import { User } from '../types/user';

interface LoginResponse {
    access_token: string;
    refresh_token?: string;
    token_type: string;
}

const login = async (credentials: LoginFormInputs): Promise<LoginResponse> => {
  const formData = new URLSearchParams();
  formData.append('username', credentials.email);
  formData.append('password', credentials.password);

  const response = await apiClient.post<LoginResponse>('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
};

const fetchCurrentUser = async (): Promise<User> => {
  const response = await apiClient.get<User>('/users/me');
  return response.data;
};

const refreshToken = async (currentRefreshToken: string): Promise<Token> => {
    const response = await apiClient.post<Token>('/auth/refresh', {
        refresh_token: currentRefreshToken
    });
    return response.data;
};

export const authService = {
  login,
  fetchCurrentUser,
  refreshToken,
};
