export type MessageRole = 'user' | 'bot';
export type ConversationRating = 'positive' | 'negative' | null;

export interface Source {
  name: string;
  category: string;
  origin: string;
  date: string;
  version: string;
  excerpt: string;
}

export interface Midia {
  tipo: string;
  preview_url: string;
  nome: string;
  artista: string;
  url: string;
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  sources?: Source[];
  midia?: Midia | null;
  streaming?: boolean;
  respostaId?: number;
  feedbackId?: number | null;
  feedbackTipo?: 'like' | 'dislike' | null;
}

export interface Conversation {
  id: string;
  title: string;
  updatedAt: string;
  messages: Message[];
}

export interface ChatApiResponse {
  id: string | number;
  titulo: string;
  updated_at: string;
}

export type DashboardPeriod = 'today' | 'week' | 'month';
export type ExportFormat = 'pdf' | 'csv' | 'json';
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

export interface UserProfile {
  name: string;
  email: string;
  avatar: string;
  plan: string;
  followers: number;
}

export interface Track {
  name: string;
  artist: string;
  album: string;
  played_at: string;
  preview_url: string | null;
  spotify_url: string | null;
}

export interface Device {
  id: string;
  name: string;
  type: string;
  is_active: boolean;
}

export type UserRole = 'user' | 'moderator';

export interface User {
  name: string;
  email: string;
  avatar: string;
  role: UserRole;
  plan?: string;
  followers?: number;
  superUsuarioId?: number | null;
}