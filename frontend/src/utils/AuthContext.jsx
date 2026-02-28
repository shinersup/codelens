import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { auth as authApi } from './api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Restore session on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('codelens_token');
    const savedUser = localStorage.getItem('codelens_user');
    if (savedToken && savedUser) {
      try {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
      } catch {
        localStorage.removeItem('codelens_token');
        localStorage.removeItem('codelens_user');
      }
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (email, password) => {
    const response = await authApi.login(email, password);
    const { access_token } = response.data;

    // We don't get full user info from login, store email
    const userData = { email };
    localStorage.setItem('codelens_token', access_token);
    localStorage.setItem('codelens_user', JSON.stringify(userData));

    setToken(access_token);
    setUser(userData);
    return response.data;
  }, []);

  const register = useCallback(async (username, email, password) => {
    const response = await authApi.register(username, email, password);
    return response.data;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('codelens_token');
    localStorage.removeItem('codelens_user');
    setToken(null);
    setUser(null);
  }, []);

  const isAuthenticated = !!token;

  return (
    <AuthContext.Provider
      value={{ user, token, login, register, logout, loading, isAuthenticated }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
