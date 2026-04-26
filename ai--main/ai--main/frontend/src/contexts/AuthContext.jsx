import { createContext, useContext, useEffect, useState } from 'react';

import api from '../services/api';


const AuthContext = createContext(null);


const cleanToken = (token) => {
  if (!token) return null;
  return String(token).replace(/[^\x00-\x7F]/g, '').trim();
};


export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchMe = async (token) => {
    try {
      const clean = cleanToken(token);
      if (!clean) return null;

      const res = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${clean}` },
      });

      return { token: clean, ...res.data };
    } catch (error) {
      console.error('fetchMe error:', error);
      return null;
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        setLoading(false);
        return;
      }

      const clean = cleanToken(token);
      if (clean !== token) {
        localStorage.setItem('token', clean);
      }

      const userData = await fetchMe(clean);
      if (userData) {
        setUser(userData);
      } else {
        localStorage.removeItem('token');
        setUser(null);
      }

      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (username, password) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    const res = await api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    const token = cleanToken(res.data.access_token);
    localStorage.setItem('token', token);

    const userData = await fetchMe(token);
    if (!userData?.id) {
      localStorage.removeItem('token');
      setUser(null);
      throw new Error('Login succeeded but the user profile could not be loaded');
    }

    setUser(userData);
    return true;
  };

  const register = async (username, email, password) => {
    const res = await api.post('/auth/register', { username, email, password });
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}


export const useAuth = () => useContext(AuthContext);
