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
  loginWithProfile: (profile: UserProfile, jwt: string, refreshJwt?: string) => void;
  loginWithToken: (jwt: string, refreshJwt?: string) => Promise<boolean>;
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
const REFRESH_TOKEN_KEY = 'musicbot_refresh_jwt';
const INACTIVITY_TIMEOUT_MS = 15 * 60 * 1000; // 15 minutos

export const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be inside AuthProvider');
  return ctx;
};

// ── Helpers globais ──────────────────────────────────────────────────────────

let _globalLogout: (() => void) | null = null;

/** Retorna o access token atual (pode ser usado por authFetch antes do provider montar) */
function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

function setTokens(access: string, refresh?: string) {
  localStorage.setItem(TOKEN_KEY, access);
  if (refresh) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  }
}

function clearTokens() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/** Tenta renovar o access token. Retorna o novo token ou null. */
async function attemptRefresh(): Promise<string | null> {
  const refreshJwt = getRefreshToken();
  if (!refreshJwt) return null;

  try {
    const res = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${refreshJwt}`,
      },
    });
    if (!res.ok) return null;
    const body = await res.json();
    const newAccess = body.data?.token || body.token;
    if (newAccess) {
      localStorage.setItem(TOKEN_KEY, newAccess);
      return newAccess;
    }
  } catch {
    // Rede offline
  }
  return null;
}

// ── Inactivity Timer ─────────────────────────────────────────────────────────

let inactivityTimer: ReturnType<typeof setTimeout> | null = null;

function resetInactivityTimer() {
  if (inactivityTimer) clearTimeout(inactivityTimer);
  if (!getAccessToken()) return; // não logado
  inactivityTimer = setTimeout(() => {
    console.log('[Inactivity] 15min sem atividade — logout automático');
    if (_globalLogout) _globalLogout();
  }, INACTIVITY_TIMEOUT_MS);
}

function clearInactivityTimer() {
  if (inactivityTimer) {
    clearTimeout(inactivityTimer);
    inactivityTimer = null;
  }
}

// Escuta eventos de atividade do usuário
const activityEvents = ['mousedown', 'keydown', 'touchstart', 'scroll', 'mousemove'];
function setupActivityListeners() {
  activityEvents.forEach((evt) => {
    document.addEventListener(evt, resetInactivityTimer, { passive: true });
  });
}

function removeActivityListeners() {
  activityEvents.forEach((evt) => {
    document.removeEventListener(evt, resetInactivityTimer);
  });
}

// ── authFetch com interceptor 401 ────────────────────────────────────────────

/** Faz fetch autenticado. Se receber 401, tenta renovar token e retry. */
export async function authFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const jwt = getAccessToken();

  const doFetch = (token: string | null) =>
    fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

  const res = await doFetch(jwt);
  resetInactivityTimer();

  // Se não é 401 ou não temos refresh token, retorna direto
  if (res.status !== 401 || !getRefreshToken()) {
    return res;
  }

  // Tenta renovar o access token
  const newToken = await attemptRefresh();
  if (!newToken) {
    // Refresh também expirou — força logout
    if (_globalLogout) _globalLogout();
    return res; // retorna o 401 original
  }

  // Retry com novo token
  return doFetch(newToken);
}

// ── Provider ─────────────────────────────────────────────────────────────────

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));

  /** Busca role e super_usuario_id do backend via /api/auth/me */
  async function fetchMeData(jwt: string): Promise<MeResponse | null> {
    try {
      const res = await authFetch('/api/auth/me');
      if (!res.ok) return null;
      const data = await res.json();
      return data.data ?? data;
    } catch {
      return null;
    }
  }

  // Valida token ao montar e inicia timer de inatividade
  useEffect(() => {
    setupActivityListeners();
    if (token && !user) {
      _loadProfile(token).catch(() => logout());
    }
    resetInactivityTimer();

    return () => {
      removeActivityListeners();
      clearInactivityTimer();
    };
  }, []);

  /** Carrega perfil do Spotify + role a partir do JWT */
  async function _loadProfile(jwt: string): Promise<void> {
    const meData = await fetchMeData(jwt);
    if (!meData) throw new Error('invalid token');

    const role: UserRole = meData.role === 'moderator' ? 'moderator' : 'user';
    const superUsuarioId = meData.super_usuario_id ?? null;

    try {
      const res = await authFetch('/api/spotify/profile');
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

  const _saveToken = (jwt: string, refreshJwt?: string) => {
    setTokens(jwt, refreshJwt);
    setToken(jwt);
    resetInactivityTimer();
  };

  /** Usado após callback Spotify ou register (temos o perfil na mão) */
  const loginWithProfile = useCallback((profile: UserProfile, jwt: string, refreshJwt?: string) => {
    _saveToken(jwt, refreshJwt);
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
  const loginWithToken = useCallback(async (jwt: string, refreshJwt?: string): Promise<boolean> => {
    try {
      // Salva tokens ANTES de chamar fetchMeData, pois ela usa authFetch
      _saveToken(jwt, refreshJwt);

      const meData = await fetchMeData(jwt);
      if (!meData) throw new Error('invalid token');

      const role: UserRole = meData.role === 'moderator' ? 'moderator' : 'user';
      const superUsuarioId = meData.super_usuario_id ?? null;

      // Tenta carregar o perfil do Spotify automaticamente
      try {
        const res = await authFetch('/api/spotify/profile');
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
    clearTokens();
    clearInactivityTimer();
    setToken(null);
    setUser(null);
  }, []);

  // Registra o logout global para uso no authFetch e inactivity timer
  useEffect(() => {
    _globalLogout = logout;
    return () => {
      if (_globalLogout === logout) _globalLogout = null;
    };
  }, [logout]);

  const isModerator = user?.role === 'moderator';

  return (
    <AuthContext.Provider
      value={{ user, token, loginWithProfile, loginWithToken, logout, isLoggedIn: !!token, isModerator }}
    >
      {children}
    </AuthContext.Provider>
  );
};