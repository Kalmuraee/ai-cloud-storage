import { createContext, useState, useContext, ReactNode } from 'react';
import axios from 'axios';

interface AuthContextValue {
  user: any;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    username: string,
    password: string,
    fullName: string
  ) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<any>(null);

  const login = async (email: string, password: string) => {
    const response = await axios.post('/api/auth/login', { email, password });
    setUser(response.data.user);
    localStorage.setItem('accessToken', response.data.accessToken);
  };

  const register = async (
    email: string,
    username: string,
    password: string,
    fullName: string
  ) => {
    await axios.post('/api/auth/register', { email, username, password, fullName });
  };

  const logout = async () => {
    setUser(null);
    localStorage.removeItem('accessToken');
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};