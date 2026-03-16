import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import type { UserProfile } from '@/services/authService';

export type UserRole = 'user' | 'moderator';

export interface User {
  name: string;
  email: string;
  avatar: string;
  role: UserRole;
  plan?: string;
  followers?: number;
}

interface AuthContextType {
  user: User | null;
  login: (role: UserRole) => void;
  loginWithProfile: (profile: UserProfile) => void;
  logout: () => void;
  isLoggedIn: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be inside AuthProvider');
  return ctx;
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);

  const login = (role: UserRole) => {
    setUser({
      name: 'João Silva',
      email: 'joao@email.com',
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=joao',
      role,
    });
  };

  const loginWithProfile = useCallback((profile: UserProfile) => {
    setUser({
      name: profile.name,
      email: profile.email,
      avatar: profile.avatar,
      role: 'user',
      plan: profile.plan,
      followers: profile.followers,
    });
  }, []);

  const logout = () => setUser(null);

  return (
    <AuthContext.Provider value={{ user, login, loginWithProfile, logout, isLoggedIn: !!user }}>
      {children}
    </AuthContext.Provider>
  );
};
