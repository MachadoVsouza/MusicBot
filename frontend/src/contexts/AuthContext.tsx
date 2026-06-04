import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  ReactNode,
} from 'react';
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
  token: string | null;
  loginWithProfile: (profile: UserProfile, jwt: string) => void;
  loginWithToken: (jwt: string) => Promise<boolean>;
  logout: () => void;
  isLoggedIn: boolean;
}

const TOKEN_KEY = 'musicbot_jwt';

export const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be inside AuthProvider');
  return ctx;
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));

  /** Valida o token salvo ao montar (ex: reload de página) */
  useEffect(() => {
    if (token && !user) {
      fetchMe(token).catch(() => logout());
    }
  }, []);

  async function fetchMe(jwt: string): Promise<void> {
    const res = await fetch('/api/auth/me', {
      headers: { Authorization: `Bearer ${jwt}` },
    });
    if (!res.ok) throw new Error('invalid token');
    // /auth/me só retorna usuario_id; o perfil completo já deve estar
    // carregado ou pode ser buscado em /spotify/profile se necessário
  }

  const _saveToken = (jwt: string) => {
    localStorage.setItem(TOKEN_KEY, jwt);
    setToken(jwt);
  };

  /** Usado após callback Spotify ou register (temos o perfil na mão) */
  const loginWithProfile = useCallback((profile: UserProfile, jwt: string) => {
    _saveToken(jwt);
    setUser({
      name:      profile.name,
      email:     profile.email,
      avatar:    profile.avatar,
      role:      'moderator',
      plan:      profile.plan,
      followers: profile.followers,
    });
  }, []);

  /** Usado após login-custom ou callback Spotify (não temos o perfil, só o JWT) */
  const loginWithToken = useCallback(async (jwt: string): Promise<boolean> => {
    try {
      await fetchMe(jwt);
      _saveToken(jwt);
      // Tenta carregar o perfil do Spotify automaticamente
      try {
        const res = await fetch('/api/spotify/profile', {
          headers: { Authorization: `Bearer ${jwt}` },
        });
        if (res.ok) {
          const data = await res.json();
          const profile = data.data ?? data;
          setUser({
            name:      profile.display_name ?? profile.name ?? '',
            email:     profile.email ?? '',
            avatar:    profile.avatar ?? profile.images?.[0]?.url ?? '',
            role:      'moderator',
            plan:      profile.plan ?? profile.product ?? 'free',
            followers: profile.followers?.total ?? profile.followers ?? 0,
          });
        }
      } catch {
        // Perfil Spotify não disponível (login custom) — continua sem user
      }
      return true;
    } catch {
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, token, loginWithProfile, loginWithToken, logout, isLoggedIn: !!token }}
    >
      {children}
    </AuthContext.Provider>
  );
};

/** Helper para fazer fetch autenticado em qualquer lugar do app */
export function authFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const jwt = localStorage.getItem(TOKEN_KEY);
  return fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
      ...(jwt ? { Authorization: `Bearer ${jwt}` } : {}),
    },
  });
}
