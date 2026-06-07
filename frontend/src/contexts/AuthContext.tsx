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
  superUsuarioId?: number | null;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loginWithProfile: (profile: UserProfile, jwt: string) => void;
  loginWithToken: (jwt: string) => Promise<boolean>;
  logout: () => void;
  isLoggedIn: boolean;
  isModerator: boolean;
}

interface MeResponse {
  usuario_id: string;
  role: 'user' | 'moderator';
  super_usuario_id: number | null;
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

  /** Busca role e super_usuario_id do backend via /api/auth/me */
  async function fetchMeData(jwt: string): Promise<MeResponse | null> {
    try {
      const res = await fetch('/api/auth/me', {
        headers: { Authorization: `Bearer ${jwt}` },
      });
      if (!res.ok) return null;
      const data = await res.json();
      return data.data ?? data;
    } catch {
      return null;
    }
  }

  /** Valida o token salvo ao montar (ex: reload de página) e tenta carregar perfil */
  useEffect(() => {
    if (token && !user) {
      _loadProfile(token).catch(() => logout());
    }
  }, []);

  /** Carrega perfil do Spotify + role a partir do JWT */
  async function _loadProfile(jwt: string): Promise<void> {
    // Busca dados do /api/auth/me (role, super_usuario_id)
    const meData = await fetchMeData(jwt);
    if (!meData) throw new Error('invalid token');

    const role: UserRole = meData.role === 'moderator' ? 'moderator' : 'user';
    const superUsuarioId = meData.super_usuario_id ?? null;

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
          role,
          plan:      profile.plan ?? profile.product ?? 'free',
          followers: profile.followers?.total ?? profile.followers ?? 0,
          superUsuarioId,
        });
        return;
      }
    } catch {
      // Perfil Spotify indisponível
    }

    // Fallback: sem perfil Spotify, mas com role definida
    setUser({
      name: meData.usuario_id.slice(0, 8),
      email: '',
      avatar: `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(meData.usuario_id)}`,
      role,
      superUsuarioId,
    });
  }

  const _saveToken = (jwt: string) => {
    localStorage.setItem(TOKEN_KEY, jwt);
    setToken(jwt);
  };

  /** Usado após callback Spotify ou register (temos o perfil na mão) */
  const loginWithProfile = useCallback((profile: UserProfile, jwt: string) => {
    _saveToken(jwt);
    // Após salvar o token, carregar role do /api/auth/me
    fetchMeData(jwt).then((meData) => {
      const role: UserRole = meData?.role === 'moderator' ? 'moderator' : 'user';
      setUser({
        name:      profile.name,
        email:     profile.email,
        avatar:    profile.avatar,
        role,
        plan:      profile.plan,
        followers: profile.followers,
        superUsuarioId: meData?.super_usuario_id ?? null,
      });
    }).catch(() => {
      setUser({
        name:      profile.name,
        email:     profile.email,
        avatar:    profile.avatar,
        role:      'user',
        plan:      profile.plan,
        followers: profile.followers,
        superUsuarioId: null,
      });
    });
  }, []);

  /** Usado após login-custom ou callback Spotify (não temos o perfil, só o JWT) */
  const loginWithToken = useCallback(async (jwt: string): Promise<boolean> => {
    try {
      // Busca dados do /api/auth/me (role, super_usuario_id)
      const meData = await fetchMeData(jwt);
      if (!meData) throw new Error('invalid token');

      _saveToken(jwt);
      const role: UserRole = meData.role === 'moderator' ? 'moderator' : 'user';
      const superUsuarioId = meData.super_usuario_id ?? null;

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
            role,
            plan:      profile.plan ?? profile.product ?? 'free',
            followers: profile.followers?.total ?? profile.followers ?? 0,
            superUsuarioId,
          });
          return true;
        }
      } catch {
        // Perfil Spotify não disponível (login custom)
      }

      // Fallback sem perfil Spotify
      setUser({
        name: meData.usuario_id.slice(0, 8),
        email: '',
        avatar: `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(meData.usuario_id)}`,
        role,
        superUsuarioId,
      });
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

  const isModerator = user?.role === 'moderator';

  return (
    <AuthContext.Provider
      value={{ user, token, loginWithProfile, loginWithToken, logout, isLoggedIn: !!token, isModerator }}
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