// src/types/auth.ts
import { User } from './user';

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  isLoading: boolean; // To handle async auth check on app load
  error: string | null;
}

export interface AuthContextType extends AuthState {
  login: (token: string, user: User) => void;
  logout: () => void;
  // initializeAuth?: () => Promise<void>; // Optional: if we want to expose re-init or /me call
  // setUser: (user: User | null) => void; // If direct user setting is needed
  // setError: (error: string | null) => void; // If error setting is needed
}
