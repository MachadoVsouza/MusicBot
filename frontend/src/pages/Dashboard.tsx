import { useState } from 'react';
import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';
import {
  BarChart3,
  Bug,
  CheckCircle,
  FileDown,
  Lightbulb,
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

type PeriodFilter = 'today' | 'week' | 'month';
type ReviewFilter = 'all' | 'positive' | 'negative';
type FeedbackFilter = 'all' | 'bug' | 'suggestion' | 'general';
type FeedbackType = Exclude<FeedbackFilter, 'all'>;
type ReviewType = Exclude<ReviewFilter, 'all'>;

interface FeedbackRow {
  id: string;
  type: FeedbackType;
  user: string;
  message: string;
  conversation: string;
  date: string;
}

interface ReviewRow {
  id: string;
  user: string;
  rating: ReviewType;
  date: string;
}

const chartPlaceholderData = Array.from({ length: 7 }, (_, index) => ({
  slot: `${index}`,
  perguntas: null,
}));

const feedbackRows: FeedbackRow[] = [];
const reviewRows: ReviewRow[] = [];

const feedbackTypeConfig: Record<
  FeedbackType,
  { label: string; icon: LucideIcon; className: string }
> = {
  bug: { label: 'Bug', icon: Bug, className: 'text-[#E91429]' },
  suggestion: { label: 'Sugestão', icon: Lightbulb, className: 'text-white' },
  general: { label: 'Geral', icon: MessageCircle, className: 'text-[#1ED760]' },
};

const Dashboard = () => {
  const [period, setPeriod] = useState<PeriodFilter>('week');
  const [reviewFilter, setReviewFilter] = useState<ReviewFilter>('all');
  const [feedbackFilter, setFeedbackFilter] = useState<FeedbackFilter>('all');

  const filteredFeedbacks = feedbackRows.filter((feedback) => (
    feedbackFilter === 'all' || feedback.type === feedbackFilter
  ));

  const filteredReviews = reviewRows.filter((review) => (
    reviewFilter === 'all' || review.rating === reviewFilter
  ));

  return (
    <div className="min-h-screen bg-midnight music-texture p-4 md:p-8">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="mx-auto max-w-7xl"
      >
        <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <h1 className="font-display text-2xl font-bold text-off-white">
                Dashboard do MusicBot
              </h1>
              <span className="rounded-tag bg-[#1DB954] px-2 py-0.5 text-xs font-mono-label font-semibold text-black">
                Moderador
              </span>
            </div>
            <p className="max-w-2xl text-sm font-body leading-6 text-slate">
              Interface pronta para receber métricas, gráfico, feedbacks, avaliações e exportação
              assim que o backend e o banco estiverem integrados.
            </p>
          </div>

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

        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            icon={MessageSquare}
            value="--"
            label="Total de Perguntas"
            helper="Aguardando dados do banco"
          />
          <MetricCard
            icon={CheckCircle}
            value="--"
            label="Taxa de Sucesso"
            helper="Aguardando dados do banco"
          />
          <MetricCard
            icon={RefreshCw}
            value="--"
            label="Taxa de Reformulação"
            helper="Aguardando dados do banco"
          />
          <MetricCard
            icon={BarChart3}
            value="--"
            label="Conversas Validadas"
            helper="Aguardando dados do banco"
          />
        </div>

        <div className="bg-[#181818] border border-[#282828] mb-8 rounded-card p-6">
          <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <h2 className="font-display text-lg font-semibold text-off-white">Uso por Período</h2>
            <span className="text-xs font-body text-slate">
              Gráfico pronto para perguntas por dia
            </span>
          </div>

          <div className="relative h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartPlaceholderData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsla(0,0%,100%,0.06)" />
                <XAxis dataKey="slot" hide />
                <YAxis hide />
                <Tooltip
                  cursor={false}
                  contentStyle={{
                    background: 'hsla(220,30%,10%,0.95)',
                    border: '1px solid hsla(0,0%,100%,0.1)',
                    borderRadius: '12px',
                    color: 'hsl(230,20%,97%)',
                    fontFamily: 'DM Sans',
                    fontSize: '13px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="perguntas"
                  stroke="#1DB954"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                  connectNulls={false}
                />
              </LineChart>
            </ResponsiveContainer>

            <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
              <div className="rounded-card border border-[hsla(0,0%,100%,0.1)] bg-[#181818CC] px-6 py-5 text-center">
                <p className="font-display text-lg font-semibold text-off-white">
                  Gráfico aguardando integração
                </p>
                <p className="mt-2 max-w-md text-sm font-body leading-6 text-slate">
                  Este bloco já está preparado para exibir perguntas por dia sem usar datas de
                  exemplo agora.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-[#181818] border border-[#282828] mb-8 rounded-card p-6">
          <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="font-display text-lg font-semibold text-off-white">
              Feedbacks dos Usuários
            </h2>
            <div className="flex flex-wrap gap-2">
              {[
                { key: 'all' as const, label: 'Todos' },
                { key: 'bug' as const, label: 'Bugs' },
                { key: 'suggestion' as const, label: 'Sugestões' },
                { key: 'general' as const, label: 'Gerais' },
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
                  <th className="p-3 text-left text-xs font-mono-label uppercase tracking-wider text-slate">Mensagem</th>
                  <th className="p-3 text-left text-xs font-mono-label uppercase tracking-wider text-slate">Conversa</th>
                  <th className="p-3 text-left text-xs font-mono-label uppercase tracking-wider text-slate">Data</th>
                </tr>
              </thead>
              <tbody>
                {filteredFeedbacks.length === 0 ? (
                  <EmptyTableRow
                    colSpan={6}
                    title="Nenhum feedback disponível"
                    description="Os registros desta tabela serão preenchidos futuramente com os dados vindos do banco."
                  />
                ) : (
                  filteredFeedbacks.map((feedback) => {
                    const config = feedbackTypeConfig[feedback.type];
                    const TypeIcon = config.icon;

                    return (
                      <tr
                        key={feedback.id}
                        className="border-b border-[#1E1E1E] transition-colors hover:bg-[#282828]"
                      >
                        <td className="p-3 text-sm font-mono-label text-teal">{feedback.id}</td>
                        <td className="p-3">
                          <span className={`flex items-center gap-1.5 text-xs font-body ${config.className}`}>
                            <TypeIcon size={14} />
                            {config.label}
                          </span>
                        </td>
                        <td className="p-3 text-sm font-body text-off-white">{feedback.user}</td>
                        <td className="p-3 text-sm font-body text-off-white">{feedback.message}</td>
                        <td className="p-3 text-xs font-body text-slate">{feedback.conversation}</td>
                        <td className="p-3 text-xs font-mono-label text-slate">{feedback.date}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          <p className="mt-3 text-xs font-body text-slate">
            Mostrando {filteredFeedbacks.length} de {feedbackRows.length} feedbacks
          </p>
        </div>

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
                {filteredReviews.length === 0 ? (
                  <EmptyTableRow
                    colSpan={4}
                    title="Nenhuma avaliação disponível"
                    description="Os thumbs up e thumbs down desta tabela serão abastecidos futuramente pelo banco."
                  />
                ) : (
                  filteredReviews.map((review) => (
                    <tr
                      key={review.id}
                      className="border-b border-[#1E1E1E] transition-colors hover:bg-[#282828]"
                    >
                      <td className="p-3 text-sm font-mono-label text-teal">{review.id}</td>
                      <td className="p-3 text-sm font-body text-off-white">{review.user}</td>
                      <td className="p-3">
                        {review.rating === 'positive' ? (
                          <ThumbsUp size={16} className="text-teal" />
                        ) : (
                          <ThumbsDown size={16} className="text-magenta" />
                        )}
                      </td>
                      <td className="p-3 text-xs font-mono-label text-slate">{review.date}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

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
      <span className="text-xs font-mono-label text-slate">sem dados</span>
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
