import { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

// 清理 token 中的非 ASCII 字符
const cleanToken = (token) => {
  if (!token) return null;
  return token.replace(/[^\x00-\x7F]/g, '');
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchMe = async (token) => {
    try {
      const clean = cleanToken(token);
      if (!clean) return null;
      
      const res = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${clean}` }
      });
      return { token: clean, ...res.data };
    } catch (error) {
      console.error('fetchMe error:', error);
      return { token: cleanToken(token) };
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        const clean = cleanToken(token);
        if (clean !== token) {
          localStorage.setItem('token', clean);
        }
        const userData = await fetchMe(clean);
        setUser(userData);
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
    
    const token = res.data.access_token;
    const clean = cleanToken(token);
    localStorage.setItem('token', clean);
    
    // 获取用户信息并设置完整用户状态
    const userData = await fetchMe(clean);
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