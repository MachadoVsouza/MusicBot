import { useCallback, useEffect, useRef, useState } from 'react';
import {
  fetchBugs,
  fetchChartData,
  fetchFeedbacks,
  fetchMetrics,
} from '@/services/dashboardService';
import type { ChartPoint, DashboardBug, DashboardFeedback, DashboardMetrics, DashboardPeriod, PaginatedResponse } from '@/types';

interface PaginationState {
  page: number;
  totalPages: number;
  total: number;
  perPage: number;
}

interface DashboardData {
  metrics: DashboardMetrics | null;
  chartData: ChartPoint[];
  feedbacks: DashboardFeedback[];
  feedbacksPagination: PaginationState;
  bugs: DashboardBug[];
  bugsPagination: PaginationState;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  refresh: () => void;
  setFeedbackPage: (page: number) => void;
  setBugPage: (page: number) => void;
  orderBy: 'id' | 'created_at';
  setOrderBy: (order: 'id' | 'created_at') => void;
}

const PER_PAGE = 20;
const AUTO_REFRESH_MS = 30_000;

export function useDashboard(
  period: DashboardPeriod,
  feedbackTipo?: 'like' | 'dislike',
): DashboardData {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  const [feedbacks, setFeedbacks] = useState<DashboardFeedback[]>([]);
  const [feedbacksPagination, setFeedbacksPagination] = useState<PaginationState>({ page: 1, totalPages: 1, total: 0, perPage: PER_PAGE });
  const [bugs, setBugs] = useState<DashboardBug[]>([]);
  const [bugsPagination, setBugsPagination] = useState<PaginationState>({ page: 1, totalPages: 1, total: 0, perPage: PER_PAGE });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [orderBy, setOrderBy] = useState<'id' | 'created_at'>('created_at');
  const refreshTokenRef = useRef(0);

  // Páginas atuais
  const feedbackPageRef = useRef(1);
  const bugPageRef = useRef(1);
  const orderByRef = useRef<'id' | 'created_at'>('created_at');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const token = ++refreshTokenRef.current;

    try {
      const [m, c, f, b] = await Promise.all([
        fetchMetrics(period),
        fetchChartData(period),
        fetchFeedbacks(period, feedbackTipo, feedbackPageRef.current, PER_PAGE, orderByRef.current),
        fetchBugs(period, bugPageRef.current, PER_PAGE),
      ]);

      if (token !== refreshTokenRef.current) return;

      setMetrics(m);
      setChartData(c);

      setFeedbacks(f.items);
      setFeedbacksPagination({ page: f.page, totalPages: f.total_pages, total: f.total, perPage: f.per_page });

      setBugs(b.items);
      setBugsPagination({ page: b.page, totalPages: b.total_pages, total: b.total, perPage: b.per_page });

      setLastUpdated(new Date());
    } catch (err) {
      if (token !== refreshTokenRef.current) return;
      setError(err instanceof Error ? err.message : 'Erro ao carregar dados');
    } finally {
      if (token === refreshTokenRef.current) setLoading(false);
    }
  }, [period, feedbackTipo]);

  // Reseta páginas + ordenação ao trocar período/filtro
  useEffect(() => {
    feedbackPageRef.current = 1;
    bugPageRef.current = 1;
    orderByRef.current = orderBy;
    void load();
  }, [load, orderBy]);

  // Auto-refresh a cada 30s
  useEffect(() => {
    const interval = setInterval(() => {
      void load();
    }, AUTO_REFRESH_MS);
    return () => clearInterval(interval);
  }, [load]);

  const setFeedbackPage = useCallback((page: number) => {
    feedbackPageRef.current = page;
    void load();
  }, [load]);

  const setBugPage = useCallback((page: number) => {
    bugPageRef.current = page;
    void load();
  }, [load]);

  const refresh = useCallback(() => {
    void load();
  }, [load]);

  return {
    metrics,
    chartData,
    feedbacks,
    feedbacksPagination,
    bugs,
    bugsPagination,
    loading,
    error,
    lastUpdated,
    refresh,
    setFeedbackPage,
    setBugPage,
    orderBy,
    setOrderBy,
  };
}