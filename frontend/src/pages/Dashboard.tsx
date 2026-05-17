import { useState } from 'react';
import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';
import {
  AlertCircle,
  BarChart3,
  Bug,
  CheckCircle,
  FileDown,
  Lightbulb,
  Loader2,
  MessageCircle,
  MessageSquare,
  RefreshCw,
  ThumbsDown,
  ThumbsUp,
} from 'lucide-react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useDashboard } from '../hooks/useDashboard';
import type { DashboardPeriod } from '../services/dashboardService';

type ReviewFilter = 'all' | 'positive' | 'negative';
type FeedbackFilter = 'all' | 'like' | 'dislike' | 'report';
type FeedbackType = Exclude<FeedbackFilter, 'all'>;

const feedbackTypeConfig: Record<
  FeedbackType,
  { label: string; icon: LucideIcon; className: string }
> = {
  like: { label: 'Like', icon: ThumbsUp, className: 'text-[#1ED760]' },
  dislike: { label: 'Dislike', icon: ThumbsDown, className: 'text-[#E91429]' },
  report: { label: 'Report', icon: Bug, className: 'text-yellow-400' },
};

function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return '--';
  return `${value}%`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// ─── Tooltip customizado para o gráfico ──────────────────────────────────────
const ChartTooltip = ({ active, payload, label }: {
  active?: boolean;
  payload?: { value: number }[];
  label?: string;
}) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-card border border-[hsla(0,0%,100%,0.1)] bg-[#181818] px-3 py-2 text-sm">
      <p className="font-mono-label text-slate">{label}</p>
      <p className="font-display font-semibold text-[#1DB954]">{payload[0].value} perguntas</p>
    </div>
  );
};

// ─── Componente principal ─────────────────────────────────────────────────────
const Dashboard = () => {
  const [period, setPeriod] = useState<DashboardPeriod>('week');
  const [reviewFilter, setReviewFilter] = useState<ReviewFilter>('all');
  const [feedbackFilter, setFeedbackFilter] = useState<FeedbackFilter>('all');

  const { metrics, chartData, feedbacks, reviews, loading, error, refresh } = useDashboard(
    period,
    feedbackFilter === 'all' ? undefined : feedbackFilter,
    reviewFilter === 'all' ? undefined : reviewFilter,
  );

  const filteredFeedbacks = feedbacks;
  const filteredReviews = reviews;

  return (
    <div className="min-h-screen bg-midnight music-texture p-4 md:p-8">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="mx-auto max-w-7xl"
      >
        {/* ── Cabeçalho ────────────────────────────────────────────────────── */}
        <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <h1 className="font-display text-2xl font-bold text-off-white">
                Dashboard do MusicBot
              </h1>
              <span className="rounded-tag bg-[#1DB954] px-2 py-0.5 text-xs font-mono-label font-semibold text-black">
                Moderador
              </span>
              {loading && (
                <Loader2
                  size={16}
                  className="animate-spin text-slate"
                  aria-label="Carregando..."
                />
              )}
            </div>
            {error ? (
              <div className="flex items-center gap-2 text-sm text-[#E91429]">
                <AlertCircle size={14} />
                <span>{error}</span>
                <button
                  onClick={refresh}
                  className="ml-1 underline underline-offset-2 hover:text-off-white"
                >
                  Tentar novamente
                </button>
              </div>
            ) : (
              <p className="max-w-2xl text-sm font-body leading-6 text-slate">
                Métricas e dados em tempo real direto do banco de dados.
              </p>
            )}
          </div>

          {/* Filtro de período */}
          <div className="flex flex-wrap gap-2">
            {[
              { key: 'today' as const, label: 'Hoje' },
              { key: 'week' as const, label: 'Última semana' },
              { key: 'month' as const, label: 'Último mês' },
            ].map((option) => (
              <button
                key={option.key}
                onClick={() => setPeriod(option.key)}
                className={`rounded-tag px-3 py-1.5 text-sm font-body transition-all duration-200 ${
                  period === option.key
                    ? 'bg-[#1DB954] text-off-white'
                    : 'bg-[#282828] text-slate hover:text-off-white'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {/* ── Cards de métricas ─────────────────────────────────────────────── */}
        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            icon={MessageSquare}
            value={loading ? '--' : String(metrics?.total_perguntas ?? '--')}
            label="Total de Perguntas"
            helper={loading ? 'Carregando...' : `${metrics?.total_chats ?? '--'} conversas no período`}
          />
          <MetricCard
            icon={CheckCircle}
            value={loading ? '--' : formatPercent(metrics?.taxa_sucesso)}
            label="Taxa de Sucesso"
            helper={
              loading
                ? 'Carregando...'
                : `${metrics?.total_likes ?? '--'} likes · ${metrics?.total_dislikes ?? '--'} dislikes`
            }
          />
          <MetricCard
            icon={RefreshCw}
            value={loading ? '--' : formatPercent(metrics?.taxa_reformulacao)}
            label="Taxa de Reformulação"
            helper={loading ? 'Carregando...' : 'Chats com mais de 1 pergunta'}
          />
          <MetricCard
            icon={BarChart3}
            value={loading ? '--' : String(metrics?.total_chats ?? '--')}
            label="Conversas"
            helper={loading ? 'Carregando...' : 'Conversas iniciadas no período'}
          />
        </div>

        {/* ── Gráfico ───────────────────────────────────────────────────────── */}
        <div className="bg-[#181818] border border-[#282828] mb-8 rounded-card p-6">
          <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <h2 className="font-display text-lg font-semibold text-off-white">Uso por Período</h2>
            <span className="text-xs font-body text-slate">
              Perguntas por dia
            </span>
          </div>

          <div className="relative h-[280px]">
            {loading || chartData.length === 0 ? (
              <div className="flex h-full items-center justify-center">
                <div className="rounded-card border border-dashed border-[#282828] bg-[#0D0D0D] px-6 py-8 text-center">
                  {loading ? (
                    <Loader2 size={24} className="mx-auto mb-3 animate-spin text-slate" />
                  ) : (
                    <p className="font-display text-lg font-semibold text-off-white">
                      Sem dados no período
                    </p>
                  )}
                  <p className="mt-2 max-w-md text-sm font-body leading-6 text-slate">
                    {loading ? 'Carregando dados do banco...' : 'Nenhuma pergunta registrada neste período.'}
                  </p>
                </div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsla(0,0%,100%,0.06)" />
                  <XAxis
                    dataKey="dia"
                    tick={{ fill: 'hsl(220,10%,55%)', fontSize: 11, fontFamily: 'DM Mono' }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fill: 'hsl(220,10%,55%)', fontSize: 11, fontFamily: 'DM Mono' }}
                    tickLine={false}
                    axisLine={false}
                    allowDecimals={false}
                  />
                  <Tooltip content={<ChartTooltip />} />
                  <Line
                    type="monotone"
                    dataKey="perguntas"
                    stroke="#1DB954"
                    strokeWidth={2}
                    dot={{ r: 3, fill: '#1DB954', strokeWidth: 0 }}
                    activeDot={{ r: 5, fill: '#1ED760' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* ── Tabela de Feedbacks ───────────────────────────────────────────── */}
        <div className="bg-[#181818] border border-[#282828] mb-8 rounded-card p-6">
          <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="font-display text-lg font-semibold text-off-white">
              Feedbacks dos Usuários
            </h2>
            <div className="flex flex-wrap gap-2">
              {[
                { key: 'all' as const, label: 'Todos' },
                { key: 'like' as const, label: 'Likes' },
                { key: 'dislike' as const, label: 'Dislikes' },
                { key: 'report' as const, label: 'Reports' },
              ].map((option) => (
                <button
                  key={option.key}
                  onClick={() => setFeedbackFilter(option.key)}
                  className={`rounded-tag px-3 py-1 text-xs font-body transition-all duration-200 ${
                    feedbackFilter === option.key
                      ? 'bg-[#1DB954] text-off-white'
                      : 'bg-[#282828] text-gray-light hover:text-off-white'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[hsla(0,0%,100%,0.08)]">
                  <th className="p-3 text-left text-xs font-mono-label uppercase tracking-wider text-slate">ID</th>
                  <th className="p-3 text-left text-xs font-mono-label uppercase tracking-wider text-slate">Tipo</th>
                  <th className="p-3 text-left text-xs font-mono-label uppercase tracking-wider text-slate">Usuário</th>
                  <th className="p-3 text-left text-xs font-mono-label uppercase tracking-wider text-slate">Comentário</th>
                  <th className="p-3 text-left text-xs font-mono-label uppercase tracking-wider text-slate">Conversa</th>
                  <th className="p-3 text-left text-xs font-mono-label uppercase tracking-wider text-slate">Data</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center">
                      <Loader2 size={20} className="mx-auto animate-spin text-slate" />
                    </td>
                  </tr>
                ) : filteredFeedbacks.length === 0 ? (
                  <EmptyTableRow
                    colSpan={6}
                    title="Nenhum feedback disponível"
                    description="Nenhum feedback registrado para o período e filtro selecionados."
                  />
                ) : (
                  filteredFeedbacks.map((fb) => {
                    const config = feedbackTypeConfig[fb.tipo];
                    const TypeIcon = config.icon;
                    return (
                      <tr
                        key={fb.id}
                        className="border-b border-[#1E1E1E] transition-colors hover:bg-[#282828]"
                      >
                        <td className="p-3 text-sm font-mono-label text-teal">#{fb.id}</td>
                        <td className="p-3">
                          <span className={`flex items-center gap-1.5 text-xs font-body ${config.className}`}>
                            <TypeIcon size={14} />
                            {config.label}
                          </span>
                        </td>
                        <td className="p-3 text-sm font-body text-off-white">{fb.usuario_id}</td>
                        <td className="p-3 text-sm font-body text-off-white">
                          {fb.comentario || <span className="text-slate italic">sem comentário</span>}
                        </td>
                        <td className="p-3 text-xs font-body text-slate">{fb.conversa_titulo}</td>
                        <td className="p-3 text-xs font-mono-label text-slate">{formatDate(fb.created_at)}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          <p className="mt-3 text-xs font-body text-slate">
            Mostrando {filteredFeedbacks.length} feedbacks
          </p>
        </div>

        {/* ── Tabela de Avaliações ──────────────────────────────────────────── */}
        <div className="bg-[#181818] border border-[#282828] rounded-card p-6">
          <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="font-display text-lg font-semibold text-off-white">
              Avaliações Recentes
            </h2>
            <div className="flex flex-wrap gap-2">
              {[
                { key: 'all' as const, label: 'Todas' },
                { key: 'positive' as const, label: 'Positivas' },
                { key: 'negative' as const, label: 'Negativas' },
              ].map((option) => (
                <button
                  key={option.key}
                  onClick={() => setReviewFilter(option.key)}
                  className={`rounded-tag px-3 py-1 text-xs font-body transition-all duration-200 ${
                    reviewFilter === option.key
                      ? 'bg-[#1ED760] text-off-white'
                      : 'bg-[#282828] text-gray-light hover:text-off-white'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#282828]">
                  <th className="p-3 text-left text-xs font-mono-label uppercase tracking-wider text-slate">ID</th>
                  <th className="p-3 text-left text-xs font-mono-label uppercase tracking-wider text-slate">Usuário</th>
                  <th className="p-3 text-left text-xs font-mono-label uppercase tracking-wider text-slate">Avaliação</th>
                  <th className="p-3 text-left text-xs font-mono-label uppercase tracking-wider text-slate">Data</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={4} className="p-8 text-center">
                      <Loader2 size={20} className="mx-auto animate-spin text-slate" />
                    </td>
                  </tr>
                ) : filteredReviews.length === 0 ? (
                  <EmptyTableRow
                    colSpan={4}
                    title="Nenhuma avaliação disponível"
                    description="Nenhuma avaliação registrada para o período e filtro selecionados."
                  />
                ) : (
                  filteredReviews.map((rv) => (
                    <tr
                      key={rv.id}
                      className="border-b border-[#1E1E1E] transition-colors hover:bg-[#282828]"
                    >
                      <td className="p-3 text-sm font-mono-label text-teal">#{rv.id}</td>
                      <td className="p-3 text-sm font-body text-off-white">{rv.usuario_id}</td>
                      <td className="p-3">
                        {rv.avaliacao === 'positive' ? (
                          <ThumbsUp size={16} className="text-teal" />
                        ) : (
                          <ThumbsDown size={16} className="text-magenta" />
                        )}
                      </td>
                      <td className="p-3 text-xs font-mono-label text-slate">{formatDate(rv.created_at)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* ── Footer ────────────────────────────────────────────────────────── */}
        <div className="mt-6 flex justify-end">
          <button className="flex items-center gap-2 text-sm font-body text-slate transition-colors duration-200 hover:text-white">
            <FileDown size={16} />
            Exportar relatório
          </button>
        </div>
      </motion.div>
    </div>
  );
};

// ─── Sub-componentes ──────────────────────────────────────────────────────────

const MetricCard = ({
  icon: Icon,
  value,
  label,
  helper,
}: {
  icon: LucideIcon;
  value: string;
  label: string;
  helper: string;
}) => (
  <div className="bg-[#181818] border border-[#282828] rounded-card p-5 transition-all duration-200 hover:bg-[#282828]">
    <Icon size={20} className="mb-3 text-slate" />
    <div className="flex items-end justify-between gap-3">
      <div>
        <p className="font-display text-2xl font-bold text-off-white">{value}</p>
        <p className="mt-1 text-xs font-body text-slate">{label}</p>
      </div>
    </div>
    <p className="mt-3 text-xs font-body text-slate">{helper}</p>
  </div>
);

const EmptyTableRow = ({
  colSpan,
  title,
  description,
}: {
  colSpan: number;
  title: string;
  description: string;
}) => (
  <tr>
    <td colSpan={colSpan} className="p-8">
      <div className="rounded-card border border-dashed border-[#282828] bg-[#0D0D0D] px-4 py-8 text-center">
        <p className="font-display text-lg font-semibold text-off-white">{title}</p>
        <p className="mx-auto mt-2 max-w-xl text-sm font-body leading-6 text-slate">
          {description}
        </p>
      </div>
    </td>
  </tr>
);

export default Dashboard;
