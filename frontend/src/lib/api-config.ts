// frontend/src/lib/api-config.ts

/**
 * Helios Core API Configuration
 * Determines the base URL for backend communication.
 */

const API_ROOT = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

// Ensure no trailing slash
export const API_BASE_URL = API_ROOT.endsWith('/') 
  ? API_ROOT.slice(0, -1) 
  : API_ROOT;

export const getApiUrl = (path: string) => {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${cleanPath}`;
};
