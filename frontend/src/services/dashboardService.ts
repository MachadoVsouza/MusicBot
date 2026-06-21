import { authFetch } from '@/contexts/AuthContext';
import type { DashboardPeriod, ExportFormat, DashboardMetrics, ChartPoint, DashboardFeedback, DashboardBug, DashboardReview, PaginatedResponse } from '@/types';

const API = '/api';

export async function exportRelatorio(period: DashboardPeriod, format: ExportFormat = 'pdf'): Promise<void> {
  const res = await authFetch(`${API}/dashboard/export?period=${period}&format=${format}`);
  if (!res.ok) throw new Error('Falha ao exportar relatório');
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `relatorio_dashboard_${period}.${format}`;
  a.click();
  URL.revokeObjectURL(url);
}

async function apiFetch<T>(path: string): Promise<T> {
  const res = await authFetch(`${API}${path}`);
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
  page: number = 1,
  perPage: number = 20,
): Promise<PaginatedResponse<DashboardFeedback>> {
  const params = new URLSearchParams({ period, page: String(page), per_page: String(perPage) });
  if (tipo && tipo !== 'all') params.set('tipo', tipo);
  return apiFetch<PaginatedResponse<DashboardFeedback>>(`/dashboard/feedbacks?${params}`);
}

export async function fetchReviews(
  period: DashboardPeriod,
  rating?: string,
  page: number = 1,
  perPage: number = 20,
): Promise<PaginatedResponse<DashboardReview>> {
  const params = new URLSearchParams({ period, page: String(page), per_page: String(perPage) });
  if (rating && rating !== 'all') params.set('rating', rating);
  return apiFetch<PaginatedResponse<DashboardReview>>(`/dashboard/reviews?${params}`);
}

export async function fetchBugs(
  period: DashboardPeriod,
  page: number = 1,
  perPage: number = 20,
): Promise<PaginatedResponse<DashboardBug>> {
  const params = new URLSearchParams({ period, page: String(page), per_page: String(perPage) });
  return apiFetch<PaginatedResponse<DashboardBug>>(`/dashboard/bugs?${params}`);
}