import { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import type { LucideIcon } from 'lucide-react';
import {
  AlertCircle,
  ArrowLeft,
  BarChart3,
  Bug,
  CheckCircle,
  FileDown,
  Loader2,
  MessageSquare,
  RefreshCw,
  ShieldOff,
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
import { exportRelatorio } from '../services/dashboardService';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from '@/hooks/use-toast';

type ReviewFilter = 'all' | 'positive' | 'negative';
type FeedbackFilter = 'all' | 'like' | 'dislike';

const feedbackTypeConfig: Record<
  FeedbackFilter,
  { label: string; icon: LucideIcon; className: string }
> = {
  all: { label: 'Todos', icon: MessageSquare, className: 'text-slate' },
  like: { label: 'Like', icon: ThumbsUp, className: 'text-[#1ED760]' },
  dislike: { label: 'Dislike', icon: ThumbsDown, className: 'text-[#E91429]' },
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
  const navigate = useNavigate();
  const { isModerator } = useAuth();
  const [period, setPeriod] = useState<DashboardPeriod>('week');
  const [reviewFilter, setReviewFilter] = useState<ReviewFilter>('all');
  const [feedbackFilter, setFeedbackFilter] = useState<FeedbackFilter>('all');
  const [showExportMenu, setShowExportMenu] = useState(false);

  const { metrics, chartData, feedbacks, reviews, bugs, loading, error, refresh } = useDashboard(
    period,
    feedbackFilter === 'all' ? undefined : feedbackFilter,
    reviewFilter === 'all' ? undefined : reviewFilter,
  );

  const filteredFeedbacks = feedbacks;
  const filteredReviews = reviews;

  // ── Se não for moderador, mostra tela de acesso restrito ──────────────────
  if (!isModerator) {
    return (
      <div className="min-h-screen bg-midnight flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-[#181818] border border-[#282828] rounded-card p-8 text-center max-w-md w-full"
        >
          <ShieldOff size={48} className="mx-auto mb-4 text-[#E91429]" />
          <h1 className="font-display text-xl font-bold text-off-white mb-2">Acesso Restrito</h1>
          <p className="text-slate text-sm mb-6">
            O Dashboard é exclusivo para artistas e bandas verificados no Spotify.
            Se você é um artista, faça login com sua conta de artista no Spotify para acessar.
          </p>
          <button
            onClick={() => navigate('/chat')}
            className="inline-flex items-center gap-2 rounded-xl bg-[#1DB954] px-5 py-2.5 text-sm font-semibold text-white hover:brightness-110 transition-all"
          >
            <ArrowLeft size={16} /> Ir para o Chat
          </button>
        </motion.div>
      </div>
    );
  }

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
              <button
                onClick={() => navigate('/chat')}
                className="inline-flex items-center gap-1.5 rounded-xl bg-[#282828] px-3 py-1.5 text-sm font-body text-slate hover:bg-[#3E3E3E] hover:text-off-white transition-all"
                title="Voltar para o Chat"
              >
                <ArrowLeft size={16} />
                Chat
              </button>
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
                  <th className="p-3 text-left text-xs font-mono-label uppercase tracking-wider text-slate">Tipo</th>
                  <th className="p-3 text-left text-xs font-mono-label uppercase tracking-wider text-slate">Comentário</th>
                  <th className="p-3 text-left text-xs font-mono-label uppercase tracking-wider text-slate">Conversa</th>
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
                ) : filteredFeedbacks.length === 0 ? (
                  <EmptyTableRow
                    colSpan={4}
                    title="Nenhum feedback disponível"
                    description="Nenhum feedback registrado para o período e filtro selecionados."
                  />
                ) : (
                  feedbacks.map((fb) => {
                    const config = feedbackTypeConfig[fb.tipo] ?? feedbackTypeConfig.all;
                    const TypeIcon = config.icon;
                    return (
                      <tr
                        key={fb.id}
                        className="border-b border-[#1E1E1E] transition-colors hover:bg-[#282828]"
                      >
                        <td className="p-3">
                          <span className={`flex items-center gap-1.5 text-xs font-body ${config.className}`}>
                            <TypeIcon size={14} />
                            {config.label}
                          </span>
                        </td>
                        <td className="p-3 text-sm font-body text-off-white max-w-xs truncate">
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
            Mostrando {feedbacks.length} feedbacks
          </p>
        </div>

        {/* ── Tabela de Bug Reports ─────────────────────────────────────────── */}
        <div className="bg-[#181818] border border-[#282828] mb-8 rounded-card p-6">
          <div className="mb-4 flex items-center gap-2">
            <Bug size={20} className="text-yellow-400" />
            <h2 className="font-display text-lg font-semibold text-off-white">Bug Reports</h2>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[hsla(0,0%,100%,0.08)]">
                  <th className="p-3 text-left text-xs font-mono-label uppercase tracking-wider text-slate">ID</th>
                  <th className="p-3 text-left text-xs font-mono-label uppercase tracking-wider text-slate">Comentário</th>
                  <th className="p-3 text-left text-xs font-mono-label uppercase tracking-wider text-slate">Data</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={3} className="p-8 text-center">
                      <Loader2 size={20} className="mx-auto animate-spin text-slate" />
                    </td>
                  </tr>
                ) : bugs.length === 0 ? (
                  <EmptyTableRow
                    colSpan={3}
                    title="Nenhum bug reportado"
                    description="Nenhum bug report registrado para este período."
                  />
                ) : (
                  bugs.map((bug) => (
                    <tr
                      key={bug.id}
                      className="border-b border-[#1E1E1E] transition-colors hover:bg-[#282828]"
                    >
                      <td className="p-3 text-sm font-mono-label text-yellow-400">#{bug.id}</td>
                      <td className="p-3 text-sm font-body text-off-white max-w-md">
                        {bug.comentario || <span className="text-slate italic">sem comentário</span>}
                      </td>
                      <td className="p-3 text-xs font-mono-label text-slate">{formatDate(bug.created_at)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <p className="mt-3 text-xs font-body text-slate">
            Mostrando {bugs.length} bug reports
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
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowExportMenu((p) => !p)}
              className="flex items-center gap-2 text-sm font-body text-slate transition-colors duration-200 hover:text-white"
            >
              <FileDown size={16} />
              Exportar relatório
            </button>
            {showExportMenu && (
              <div className="absolute right-0 bottom-10 bg-[#282828] border border-[#3E3E3E] rounded-xl p-2 w-48 z-20">
                <p className="text-xs text-slate px-2 py-1 mb-1">Formato</p>
                {([
                  { key: 'pdf', label: 'PDF' },
                  { key: 'csv', label: 'CSV' },
                ] as const).map(({ key, label }) => (
                  <button
                    key={key}
                    type="button"
                    onClick={async () => {
                      setShowExportMenu(false);
                      try {
                        await exportRelatorio(period, key);
                        toast({ title: `Relatório ${label} exportado ✅` });
                      } catch {
                        toast({ title: 'Erro ao exportar relatório', variant: 'destructive' });
                      }
                    }}
                    className="w-full text-left px-2 py-2 rounded-lg text-off-white text-sm hover:bg-[#3E3E3E] transition-colors"
                  >
                    Exportar como {label}
                  </button>
                ))}
              </div>
            )}
          </div>
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
