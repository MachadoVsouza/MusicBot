const API_BASE = '/api';

export interface UserProfile {
  name: string;
  email: string;
  avatar: string;
  plan: string;
  followers: number;
}

export function redirectToSpotifyAuth(): void {
  window.location.href = `${API_BASE}/login`;
}

export async function getAuthenticatedUser(): Promise<UserProfile | null> {
  try {
    const res = await fetch(`${API_BASE}/profile`, {
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
  } catch {
    return null;
  }
}

export async function logout(): Promise<void> {
  try {
    await fetch(`${API_BASE}/logout`, { credentials: 'include' });
  } catch {
    // silently fail
  }
}
