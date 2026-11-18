/**
 * API client for the AML monitoring backend
 * Centralizes HTTP calls with auth token attachment and error handling
 */

const API_BASE = import.meta.env.VITE_API_URL ?? '/api';

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public correlationId?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Get the current auth token from storage
 */
function getAuthToken(): string | null {
  return sessionStorage.getItem('auth_token');
}

/**
 * Get the current user from storage
 */
export function getCurrentUser(): { id: number; username: string; role: string } | null {
  const userJson = sessionStorage.getItem('current_user');
  if (!userJson) return null;
  try {
    return JSON.parse(userJson);
  } catch {
    return null;
  }
}

/**
 * Generic fetch wrapper with auth and error handling
 */
async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = `${API_BASE}${path}`;
  const response = await fetch(url, { ...options, headers });

  if (response.status === 401) {
    // Clear token and throw to trigger redirect to login
    sessionStorage.removeItem('auth_token');
    sessionStorage.removeItem('current_user');
    throw new ApiError(401, 'UNAUTHORIZED', 'Authentication required');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      code: 'UNKNOWN_ERROR',
      message: response.statusText,
    }));
    throw new ApiError(
      response.status,
      error.code || 'API_ERROR',
      error.message || error.detail || 'Request failed',
      error.correlationId
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

/**
 * API methods
 */
export const apiClient = {
  get<T>(path: string): Promise<T> {
    return apiRequest<T>(path, { method: 'GET' });
  },

  post<T>(path: string, data?: unknown): Promise<T> {
    return apiRequest<T>(path, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  put<T>(path: string, data?: unknown): Promise<T> {
    return apiRequest<T>(path, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  patch<T>(path: string, data?: unknown): Promise<T> {
    return apiRequest<T>(path, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  delete<T>(path: string): Promise<T> {
    return apiRequest<T>(path, { method: 'DELETE' });
  },
};
