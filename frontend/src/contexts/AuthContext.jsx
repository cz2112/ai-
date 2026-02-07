import { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchMe = async (token) => {
    try {
      const res = await api.get('/auth/me');
      setUser({ token: token || localStorage.getItem('token'), ...res.data });
    } catch {
      // If /auth/me fails, keep the token-only user so PrivateRoute still works
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setUser({ token });
      fetchMe(token).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (username, password) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    const res = await api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    const token = res.data.access_token;
    localStorage.setItem('token', token);
    // Fetch user info and set complete user state
    try {
      const me = await api.get('/auth/me');
      setUser({ token, ...me.data });
    } catch {
      setUser({ token });
    }
  };

  const register = async (username, email, password) => {
    await api.post('/auth/register', { username, email, password });
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
