const API_BASE = '/api';

export interface UserProfile {
  name: string;
  email: string;
  avatar: string;
  plan: string;
  followers: number;
}

export interface RegisterData {
  email: string;
  password: string;
}

export interface RegisterResponse {
  success: boolean;
  error?: string;
  message?: string;
}

export function redirectToSpotifyAuth(): void {
  globalThis.location.href = `${API_BASE}/auth/login`;
}

export async function getAuthenticatedUser(): Promise<UserProfile | null> {
  try {
    const res = await fetch(`${API_BASE}/spotify/profile`, {
      credentials: 'include',
    });

    if (!res.ok) return null;

    const data = await res.json();

    return {
      name: data.display_name ?? data.name ?? '',
      email: data.email ?? '',
      avatar: data.avatar ?? data.images?.[0]?.url ?? '',
      plan: data.plan ?? data.product ?? 'free',
      followers: data.followers?.total ?? data.followers ?? 0,
    };
  } catch (err) {
    console.error('Erro ao buscar perfil autenticado:', err);
    return null;
  }
}

export async function registerUser(data: RegisterData): Promise<RegisterResponse> {
  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    const body = await res.json();

    if (!res.ok) {
      return {
        success: false,
        error: body.message || body.error || 'Erro ao criar conta',
      };
    }

    return { success: true };
  } catch (err) {
    console.error('Erro ao registrar usuário:', err);
    return {
      success: false,
      error: 'Erro de conexão com o servidor',
    };
  }
}

export async function logout(): Promise<void> {
  try {
    await fetch(`${API_BASE}/auth/logout`, { credentials: 'include' });
  } catch (err) {
    console.error('Erro ao fazer logout:', err);
  }
}

export interface LoginData {
  email: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  error?: string;
  message?: string;
  usuario_id?: string;
}

export async function loginWithPassword(data: LoginData): Promise<LoginResponse> {
  try {
    const res = await fetch(`${API_BASE}/auth/login-custom`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    const body = await res.json();

    if (!res.ok) {
      return {
        success: false,
        error: body.message || body.error || 'Erro ao fazer login',
      };
    }

    return { success: true, usuario_id: body.data?.usuario_id };
  } catch (err) {
    console.error('Erro ao fazer login com senha:', err);
    return {
      success: false,
      error: 'Erro de conexão com o servidor',
    };
  }
}
