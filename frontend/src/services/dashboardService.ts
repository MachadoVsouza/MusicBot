import { authFetch } from '@/contexts/AuthContext';

const API_BASE = '/api';

export type DashboardPeriod = 'today' | 'week' | 'month';
export type FeedbackTipo = 'like' | 'dislike' | 'report';
export type ReviewRating = 'positive' | 'negative';

export interface DashboardMetrics {
  total_perguntas: number;
  total_chats: number;
  taxa_sucesso: number | null;
  taxa_reformulacao: number | null;
  total_likes: number;
  total_dislikes: number;
}

export interface ChartPoint {
  dia: string;
  perguntas: number;
}

export interface DashboardFeedback {
  id: string;
  tipo: FeedbackTipo;
  usuario_id: string;
  comentario: string;
  conversa_id: string;
  conversa_titulo: string;
  created_at: string;
}

export interface DashboardReview {
  id: string;
  usuario_id: string;
  avaliacao: ReviewRating;
  created_at: string;
}

async function apiFetch<T>(path: string): Promise<T> {
  const res = await authFetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`Dashboard API error: ${res.status}`);
  return res.json() as Promise<T>;
}

export async function fetchMetrics(period: DashboardPeriod): Promise<DashboardMetrics> {
  return apiFetch(`/dashboard/metrics?period=${period}`);
}

export async function fetchChartData(period: DashboardPeriod): Promise<ChartPoint[]> {
  const body = await apiFetch<{ data: ChartPoint[] }>(`/dashboard/chart?period=${period}`);
  return body.data;
}

export async function fetchFeedbacks(
  period: DashboardPeriod,
  tipo?: string,
): Promise<DashboardFeedback[]> {
  const params = new URLSearchParams({ period });
  if (tipo && tipo !== 'all') params.set('tipo', tipo);
  const body = await apiFetch<{ feedbacks: DashboardFeedback[] }>(
    `/dashboard/feedbacks?${params}`,
  );
  return body.feedbacks;
}

export async function fetchReviews(
  period: DashboardPeriod,
  rating?: string,
): Promise<DashboardReview[]> {
  const params = new URLSearchParams({ period });
  if (rating && rating !== 'all') params.set('rating', rating);
  const body = await apiFetch<{ reviews: DashboardReview[] }>(
    `/dashboard/reviews?${params}`,
  );
  return body.reviews;
}
