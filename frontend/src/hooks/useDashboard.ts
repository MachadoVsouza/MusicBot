import { useCallback, useEffect, useRef, useState } from 'react';
import {
  fetchChartData,
  fetchFeedbacks,
  fetchMetrics,
  fetchReviews,
  type ChartPoint,
  type DashboardFeedback,
  type DashboardMetrics,
  type DashboardPeriod,
  type DashboardReview,
} from '../services/dashboardService';

interface DashboardData {
  metrics: DashboardMetrics | null;
  chartData: ChartPoint[];
  feedbacks: DashboardFeedback[];
  reviews: DashboardReview[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useDashboard(
  period: DashboardPeriod,
  feedbackTipo?: string,
  reviewRating?: string,
): DashboardData {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  const [feedbacks, setFeedbacks] = useState<DashboardFeedback[]>([]);
  const [reviews, setReviews] = useState<DashboardReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const refreshTokenRef = useRef(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const token = ++refreshTokenRef.current;

    try {
      const [m, c, f, r] = await Promise.all([
        fetchMetrics(period),
        fetchChartData(period),
        fetchFeedbacks(period, feedbackTipo),
        fetchReviews(period, reviewRating),
      ]);

      // Ignora se já houve novo refresh enquanto esperava
      if (token !== refreshTokenRef.current) return;

      setMetrics(m);
      setChartData(c);
      setFeedbacks(f);
      setReviews(r);
    } catch (err) {
      if (token !== refreshTokenRef.current) return;
      setError(err instanceof Error ? err.message : 'Erro ao carregar dados');
    } finally {
      if (token === refreshTokenRef.current) setLoading(false);
    }
  }, [period, feedbackTipo, reviewRating]);

  useEffect(() => {
    void load();
  }, [load]);

  return { metrics, chartData, feedbacks, reviews, loading, error, refresh: load };
}
