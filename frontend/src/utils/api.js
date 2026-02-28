import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT to every request if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('codelens_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Global response interceptor — handle 401 (expired token)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('codelens_token');
      localStorage.removeItem('codelens_user');
      // Only redirect if not already on auth pages
      if (
        !window.location.pathname.includes('/login') &&
        !window.location.pathname.includes('/register')
      ) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth ──
export const auth = {
  register: (username, email, password) =>
    api.post('/auth/register', { username, email, password }),

  // Backend expects JSON: { email, password } via UserLogin schema
  login: (email, password) =>
    api.post('/auth/login', { email, password }),
};

// ── Code Analysis ──
export const codeAnalysis = {
  review: (code, language) =>
    api.post('/review', { code, language }),

  explain: (code, language) =>
    api.post('/explain', { code, language }),

  refactor: (code, language) =>
    api.post('/refactor', { code, language }),
};

// ── History ──
export const history = {
  getAll: () => api.get('/history'),
  getById: (id) => api.get(`/history/${id}`),
  delete: (id) => api.delete(`/history/${id}`),
  clearAll: () => api.delete('/history'),
};

// ── Health ──
export const health = {
  check: () => api.get('/health'),
};

export default api;
