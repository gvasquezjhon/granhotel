// src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { AuthState, AuthContextType } from '../types/auth';
import { User } from '../types/user';
import { Token } from '../types/token'; // Import Token type
import { authService } from '../services/authService'; // Import authService
// apiClient is not directly used here anymore, authService encapsulates it.

const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  token: null,
  isLoading: true,
  error: null,
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>(initialState);

  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem('authToken');
      if (storedToken) {
        try {
          // Validate token by fetching current user
          // apiClient's interceptor will use the storedToken for this call
          const user = await authService.fetchCurrentUser();
          setAuthState({
            isAuthenticated: true,
            user,
            token: storedToken,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          console.error("Failed to fetch current user with stored token:", error);
          localStorage.removeItem('authToken');
          localStorage.removeItem('refreshToken'); // Also clear refresh token if main token fails
          setAuthState({ ...initialState, isLoading: false, error: "Session expired or token invalid." });
        }
      } else {
        setAuthState({ ...initialState, isLoading: false });
      }
    };
    initializeAuth();
  }, []);


  const login = (token: string, user: User, refreshTokenVal?: string) => {
    localStorage.setItem('authToken', token);
    if (refreshTokenVal) {
        localStorage.setItem('refreshToken', refreshTokenVal);
    }
    setAuthState({
      isAuthenticated: true,
      user,
      token,
      isLoading: false,
      error: null,
    });
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('refreshToken');
    setAuthState({ ...initialState, isLoading: false });
  };

  return (
    <AuthContext.Provider value={{ ...authState, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
