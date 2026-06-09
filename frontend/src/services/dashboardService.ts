import { authFetch } from '@/contexts/AuthContext';

const API_BASE = '/api';

export type DashboardPeriod = 'today' | 'week' | 'month';

const API = '/api';

export type ExportFormat = 'pdf' | 'csv' | 'json';

export async function exportRelatorio(period: DashboardPeriod, format: ExportFormat = 'pdf'): Promise<void> {
  const jwt = localStorage.getItem('musicbot_jwt');
  const res = await fetch(`${API}/dashboard/export?period=${period}&format=${format}`, {
    headers: jwt ? { Authorization: `Bearer ${jwt}` } : {},
  });
  if (!res.ok) throw new Error('Falha ao exportar relatório');
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `relatorio_dashboard_${period}.${format}`;
  a.click();
  URL.revokeObjectURL(url);
}
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
  tipo: 'like' | 'dislike';
  comentario: string;
  conversa_titulo: string;
  created_at: string;
}

export interface DashboardBug {
  id: string;
  comentario: string;
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

export async function fetchBugs(period: DashboardPeriod): Promise<DashboardBug[]> {
  const body = await apiFetch<{ bugs: DashboardBug[] }>(
    `/dashboard/bugs?period=${period}`,
  );
  return body.bugs;
}
