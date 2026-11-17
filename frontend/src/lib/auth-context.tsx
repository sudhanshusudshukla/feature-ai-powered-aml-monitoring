/**
 * Authentication context provider
 * Manages login/logout and current user state
 */
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient, ApiError } from './api-client';

export interface User {
  id: number;
  username: string;
  full_name: string;
  role: string;
}

interface LoginRequest {
  email: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore user from session storage on mount
  useEffect(() => {
    const storedUser = sessionStorage.getItem('current_user');
    const token = sessionStorage.getItem('auth_token');
    
    if (storedUser && token) {
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        sessionStorage.removeItem('current_user');
        sessionStorage.removeItem('auth_token');
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (credentials: LoginRequest) => {
    try {
      const response = await apiClient.post<LoginResponse>('/v1/auth/login', credentials);
      
      // Store token and user
      sessionStorage.setItem('auth_token', response.access_token);
      sessionStorage.setItem('current_user', JSON.stringify(response.user));
      setUser(response.user);
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new Error('Login failed');
    }
  };

  const logout = () => {
    sessionStorage.removeItem('auth_token');
    sessionStorage.removeItem('current_user');
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        logout,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
