import { FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bug, ChevronLeft, ChevronRight, Download, ExternalLink,
  MessageSquare, Music, Paperclip, Pause, Play, Settings,
  Square, Terminal, ThumbsDown, ThumbsUp, UserCircle, X,
} from 'lucide-react';
import { useAuth, authFetch } from '@/contexts/AuthContext';
import MusicbotLogo from '@/components/MusicbotLogo';

const API = '/api';
type MessageRole = 'user' | 'bot';
type ConversationRating = 'positive' | 'negative' | null;

interface Source { name: string; category: string; origin: string; date: string; version: string; excerpt: string; }
interface Midia { tipo: string; preview_url: string; nome: string; artista: string; url: string; }
interface Message { id: string; role: MessageRole; content: string; timestamp: string; sources?: Source[]; midia?: Midia | null; streaming?: boolean; respostaId?: number; }
interface Conversation { id: string; title: string; updatedAt: string; messages: Message[]; }
interface ChatApiResponse { id: string | number; titulo: string; updated_at: string; }

const DEFAULT_BOT_REPLY = 'No momento não foi possível gerar uma resposta. Tente novamente mais tarde.';
const fmt = (iso?: string) => new Date(iso ?? Date.now()).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

// ── Comandos disponíveis ────────────────────────────────────────────────────────
const COMMANDS = [
  { cmd: 'Buscar música/artista', desc: '"busca tal música" ou "procura artista X"' },
  { cmd: 'Tocar música', desc: '"toca música X" ou "play X de Y"' },
  { cmd: 'Tocar playlist', desc: '"toca minha playlist tal" ou "play playlist X"' },
  { cmd: 'Pausar/Voltar', desc: '"pausa" ou "para a música"' },
  { cmd: 'Próxima/Anterior', desc: '"próxima música" ou "volta pra anterior"' },
  { cmd: 'Adicionar na fila', desc: '"adiciona X na fila" ou "bota X depois dessa"' },
  { cmd: 'Listar playlists', desc: '"minhas playlists" ou "mostra minhas playlists"' },
  { cmd: 'Músicas curtidas', desc: '"minhas curtidas" ou "favoritos"' },
  { cmd: 'Músicas recentes', desc: '"músicas recentes" ou "últimas tocadas"' },
  { cmd: 'Top músicas/artistas', desc: '"meus top artistas" ou "mais tocadas"' },
  { cmd: 'Trocar dispositivo', desc: '"toca no celular" ou "muda pro notebook"' },
  { cmd: 'Informações gerais', desc: '"o que sabe sobre X?" (usa RAG + LLM)' },
];

// ── Mini Player ───────────────────────────────────────────────────────────────
const MiniPlayer = ({ midia }: { midia: Midia }) => {
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  const toggle = async () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (playing) {
      audio.pause();
      setPlaying(false);
      return;
    }
    try {
      setError(false);
      await audio.play();
      setPlaying(true);
    } catch {
      // URL do preview pode estar expirada ou ser bloqueada por CORS
      setError(true);
      setPlaying(false);
    }
  };

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    const onTimeUpdate = () => setProgress((audio.currentTime / audio.duration) * 100 || 0);
    const onEnded = () => { setPlaying(false); setProgress(0); };
    const onError = () => { setError(true); setPlaying(false); };
    audio.addEventListener('timeupdate', onTimeUpdate);
    audio.addEventListener('ended', onEnded);
    audio.addEventListener('error', onError);
    return () => {
      audio.removeEventListener('timeupdate', onTimeUpdate);
      audio.removeEventListener('ended', onEnded);
      audio.removeEventListener('error', onError);
    };
  }, []);

  return (
    <div className="mt-3 bg-[#181818] border border-[#3E3E3E] rounded-xl p-3 flex items-center gap-3">
      <audio ref={audioRef} src={midia.preview_url} preload="none" />
      <button type="button" onClick={toggle} className="w-9 h-9 rounded-full bg-[#1DB954] flex items-center justify-center shrink-0 hover:brightness-110 transition-all disabled:opacity-50" disabled={error}>
        {playing ? <Pause size={16} className="text-black" /> : <Play size={16} className="text-black ml-0.5" />}
      </button>
      <div className="flex-1 min-w-0">
        <p className="text-off-white text-xs font-semibold truncate">{midia.nome}</p>
        <p className="text-slate text-xs truncate">{midia.artista}</p>
        {error ? (
          <p className="text-[#E91429] text-xs mt-1">Preview indisponível</p>
        ) : (
          <div className="mt-1.5 h-1 bg-[#3E3E3E] rounded-full overflow-hidden">
            <div className="h-full bg-[#1DB954] rounded-full transition-all" style={{ width: `${progress}%` }} />
          </div>
        )}
      </div>
      <a href={midia.url} target="_blank" rel="noopener noreferrer" className="shrink-0 text-slate hover:text-[#1DB954] transition-colors" title="Abrir no Spotify">
        <Music size={16} />
      </a>
    </div>
  );
};

// ── Chat ──────────────────────────────────────────────────────────────────────
const Chat = () => {
  const navigate = useNavigate();
  const { user, logout, isModerator } = useAuth();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [conversationRating, setConversationRating] = useState<ConversationRating>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [showCommands, setShowCommands] = useState(false);
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);
  const [feedbackText, setFeedbackText] = useState('');
  const [preferences, setPreferences] = useState({ audioEnabled: true, compactMode: false });
  const [llmProvider, setLlmProvider] = useState<'local' | 'ifes'>('local');
  const [providerLoading, setProviderLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef    = useRef<HTMLTextAreaElement>(null);
  const fileInputRef   = useRef<HTMLInputElement>(null);
  const abortRef       = useRef<AbortController | null>(null);

  const resizeTextarea = () => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  };

  const displayName = useMemo(() => { if (!user?.name) return 'Visitante'; return user.name.split(' ')[0]; }, [user?.name]);
  const currentConversation = useMemo(() => conversations.find((c) => c.id === currentConversationId) ?? null, [conversations, currentConversationId]);
  const conversationTitle = currentConversation?.title ?? 'Nova conversa';
  const canNavigateConversations = conversations.length > 0;

  useEffect(() => {
    const loadChats = async () => {
      try {
        const res = await authFetch(`${API}/chat/`);
        if (!res.ok) return;
        const data = await res.json();
        setConversations((data.chats ?? []).map((c: ChatApiResponse) => ({ id: String(c.id), title: c.titulo, updatedAt: new Date(c.updated_at).toLocaleDateString('pt-BR'), messages: [] })));
      } catch { } finally { setHistoryLoading(false); }
    };
    loadChats();
  }, []);

  // Carrega o provedor LLM do usuário
  useEffect(() => {
    const loadProvider = async () => {
      try {
        const res = await authFetch(`${API}/llm-provider/`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.provider) setLlmProvider(data.provider);
      } catch { }
    };
    if (user) loadProvider();
  }, [user]);

  const toggleProvider = async () => {
    const novo = llmProvider === 'local' ? 'ifes' : 'local';
    setProviderLoading(true);
    try {
      const res = await authFetch(`${API}/llm-provider/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: novo }),
      });
      if (res.ok) setLlmProvider(novo);
    } catch { } finally { setProviderLoading(false); }
  };

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, isTyping]);
  useEffect(() => { resizeTextarea(); }, [inputValue]);

  const openDashboard     = () => { setShowSettings(false); navigate('/dashboard'); };
  const openKnowledgeBase = () => { setShowSettings(false); navigate('/base-conhecimento'); };
  const openProfile       = () => { setShowSettings(false); navigate('/profile'); };
  const handleLogout      = () => { setShowSettings(false); logout(); navigate('/login'); };

  const handleNewConversation = async () => {
    try {
      const res = await authFetch(`${API}/chat/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ titulo: 'Nova conversa' }) });
      if (!res.ok) return;
      const data = await res.json();
      const novo: Conversation = { id: String(data.chat_id), title: data.titulo, updatedAt: new Date().toLocaleDateString('pt-BR'), messages: [] };
      setConversations((prev) => [novo, ...prev]);
      setCurrentConversationId(novo.id);
      setMessages([]);
      setConversationRating(null);
      setShowHistory(false);
    } catch { }
  };

  // ── Stop streaming ──────────────────────────────────────────────────────────
  const handleStop = () => {
    abortRef.current?.abort();
    abortRef.current = null;
    setIsTyping(false);
    // Marca a última mensagem do bot como finalizada
    setMessages((prev) => prev.map((m, i) => i === prev.length - 1 && m.role === 'bot' ? { ...m, streaming: false } : m));
  };

  // ── Send message com streaming ──────────────────────────────────────────────
  const handleSendMessage = async () => {
    const text = inputValue.trim();
    if (!text && !selectedFile) return;

    let chatId = currentConversationId;
    if (!chatId) {
      try {
        const res = await authFetch(`${API}/chat/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ titulo: (text || 'Arquivo').slice(0, 50) }) });
        if (!res.ok) return;
        const data = await res.json();
        chatId = String(data.chat_id);
        setConversations((prev) => [{ id: chatId!, title: data.titulo, updatedAt: new Date().toLocaleDateString('pt-BR'), messages: [] }, ...prev]);
        setCurrentConversationId(chatId);
      } catch { return; }
    }

    const userMessage: Message = {
      id: `u-${Date.now()}`, role: 'user',
      content: selectedFile ? `${text}${text ? '\n' : ''}📎 ${selectedFile.name}` : text,
      timestamp: fmt(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setSelectedFile(null);
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    setIsTyping(true);

    // Placeholder da mensagem do bot (streaming)
    const botId = `b-${Date.now()}`;
    setMessages((prev) => [...prev, { id: botId, role: 'bot', content: '', timestamp: fmt(), streaming: true }]);

    abortRef.current = new AbortController();

    try {
      let response: Response;

      if (selectedFile) {
        // Upload de arquivo — usa rota multipart
        const form = new FormData();
        form.append('mensagem', text);
        form.append('arquivo', selectedFile);
        const jwt = localStorage.getItem('musicbot_jwt');
        response = await fetch(`${API}/chat/${chatId}/message-with-file`, {
          method: 'POST', body: form, signal: abortRef.current.signal,
          headers: jwt ? { Authorization: `Bearer ${jwt}` } : {},
        });
        const data = await response.json();
        setMessages((prev) => prev.map((m) => m.id === botId ? { ...m, content: data.resposta ?? DEFAULT_BOT_REPLY, streaming: false, midia: data.midia ?? null } : m));
      } else {
        // Streaming SSE
        response = await authFetch(`${API}/chat/${chatId}/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mensagem: text }),
          signal: abortRef.current.signal,
        });

        const reader  = response.body!.getReader();
        const decoder = new TextDecoder();
        let   buffer  = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? '';

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const json = JSON.parse(line.slice(6));

            if (json.chunk !== undefined) {
              setMessages((prev) => prev.map((m) => m.id === botId ? { ...m, content: m.content + json.chunk } : m));
            }
            if (json.done) {
              setMessages((prev) => prev.map((m) => m.id === botId ? { ...m, streaming: false, midia: json.midia ?? null, respostaId: json.resposta_id } : m));
            }
          }

          await Promise.resolve();
        }
      }
    } catch (e: unknown) {
      if (e instanceof Error && e.name !== 'AbortError') {
        setMessages((prev) => prev.map((m) => m.id === botId ? { ...m, content: DEFAULT_BOT_REPLY, streaming: false } : m));
      }
    } finally {
      setIsTyping(false);
      abortRef.current = null;
    }
  };

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => { e.preventDefault(); e.stopPropagation(); if (!isTyping) handleSendMessage(); };

  const loadConversationMessages = async (id: string) => {
    setCurrentConversationId(id);
    setMessages([]);
    try {
      const res = await authFetch(`${API}/chat/${id}/messages`);
      if (!res.ok) return;
      const data = await res.json();
      setMessages(data.messages ?? []);
    } catch { }
  };

  const handlePreviousConversation = () => {
    if (!canNavigateConversations) return;
    const idx = conversations.findIndex((c) => c.id === currentConversationId);
    const next = idx <= 0 ? conversations.length - 1 : idx - 1;
    loadConversationMessages(conversations[next].id);
  };

  const handleNextConversation = async () => {
    if (!canNavigateConversations) return;
    const idx = conversations.findIndex((c) => c.id === currentConversationId);
    const next = idx >= conversations.length - 1 ? 0 : idx + 1;
    loadConversationMessages(conversations[next].id);
  };
  const handleSelectConversation = async (id: string) => {
    setShowHistory(false);
    await loadConversationMessages(id);
  };

  // ── Feedback ──────────────────────────────────────────────────────────────────
  const sendFeedback = async (tipo: 'like' | 'dislike' | 'report', comentario: string = '') => {
    // Pega a última mensagem do bot que tenha respostaId
    const ultimaMsgBot = [...messages].reverse().find((m) => m.role === 'bot' && m.respostaId);
    if (!ultimaMsgBot?.respostaId) return;

    try {
      await authFetch(`${API}/chat/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resposta_id: ultimaMsgBot.respostaId,
          tipo,
          comentario: comentario || undefined,
        }),
      });
    } catch {
      // falha silenciosa — feedback não é crítico
    }
  };

  // ── Export ──────────────────────────────────────────────────────────────────
  const handleExport = async (format: 'txt' | 'json' | 'md' | 'pdf') => {
    if (!currentConversationId) return;
    setShowExportMenu(false);
    const res = await authFetch(`${API}/chat/${currentConversationId}/export?format=${format}`);
    if (!res.ok) return;
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `chat_${currentConversationId}.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const userAvatar = user?.avatar || `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(user?.name ?? 'U')}`;
  const userAlt    = user?.name || 'Usuário visitante';

  let historyContent: JSX.Element;
  if (historyLoading) {
    historyContent = (<div className="space-y-2"><div className="h-12 rounded-xl bg-white/10 animate-pulse" /><div className="h-12 rounded-xl bg-white/10 animate-pulse" /><div className="h-12 rounded-xl bg-white/10 animate-pulse" /></div>);
  } else if (conversations.length === 0) {
    historyContent = <p className="text-slate text-sm py-4">Nenhuma conversa encontrada.</p>;
  } else {
    historyContent = (
      <div className="space-y-2 max-h-64 overflow-auto">
        {conversations.map((c) => (
          <button key={c.id} type="button" onClick={() => handleSelectConversation(c.id)}
            className={`w-full text-left rounded-xl px-3 py-3 transition-colors ${c.id === currentConversationId ? 'bg-[#282828] text-white border-l-2 border-[#1DB954]' : 'bg-transparent text-[#B3B3B3] hover:text-white hover:bg-[#282828]'}`}>
            <p className="text-sm font-medium truncate">{c.title}</p>
            <p className="text-xs mt-0.5">{c.updatedAt}</p>
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-midnight flex flex-col">
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full px-4 sm:px-6 lg:px-8 pt-5 sm:pt-6 pb-5">
        <div className="flex justify-center mb-5 sm:mb-6"><MusicbotLogo size="sm" /></div>

        {/* Mensagens */}
        <div className="flex-1 overflow-y-auto min-h-0 space-y-4 sm:space-y-5 pb-5 sm:pb-6 pr-1">
          {messages.length === 0 ? (
            <div className="bg-[#181818] rounded-2xl p-6 sm:p-8 text-center max-w-2xl mx-auto">
              <h2 className="font-display text-xl text-off-white mb-2">Bem-vindo, {displayName}</h2>
              <p className="text-slate text-sm sm:text-base">{currentConversationId ? 'Nenhuma mensagem ainda.' : 'Envie uma mensagem para começar.'}</p>
            </div>
          ) : (
            messages.map((message) => (
              <article key={message.id} className={`w-full flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[90%] sm:max-w-[78%] rounded-2xl px-4 sm:px-5 py-3 sm:py-4 ${message.role === 'user' ? 'bg-[#1DB954] text-off-white rounded-br-md' : 'bg-[#282828] text-off-white rounded-bl-md'}`}>
                  <p className="text-sm sm:text-base whitespace-pre-wrap leading-relaxed">
                    {message.content}
                    {message.streaming && <span className="inline-block w-2 h-4 ml-1 bg-[#1DB954] animate-pulse rounded-sm" />}
                  </p>
                  {message.role === 'bot' && message.midia?.preview_url && <MiniPlayer midia={message.midia} />}
                  <div className="mt-2 text-xs text-slate flex items-center gap-2">
                    <span>{message.timestamp}</span>
                    {message.sources && message.sources.length > 0 && (
                      <button type="button" onClick={() => setSelectedSource(message.sources?.[0] ?? null)} className="text-[#1DB954] hover:underline">Fonte</button>
                    )}
                  </div>
                </div>
              </article>
            ))
          )}
          {isTyping && messages[messages.length - 1]?.streaming !== true && (
            <div className="flex items-center gap-1 bg-[#282828] rounded-2xl rounded-bl-md px-4 py-3 w-fit">
              <div className="w-2 h-2 rounded-full bg-[#1DB954] typing-dot" />
              <div className="w-2 h-2 rounded-full bg-[#1DB954] typing-dot" />
              <div className="w-2 h-2 rounded-full bg-[#1DB954] typing-dot" />
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Arquivo selecionado */}
        {selectedFile && (
          <div className="mb-2 flex items-center gap-2 px-3 py-2 bg-[#282828] rounded-xl text-sm text-off-white">
            <Paperclip size={14} className="text-[#1DB954]" />
            <span className="truncate flex-1">{selectedFile.name}</span>
            <button type="button" onClick={() => setSelectedFile(null)} className="text-slate hover:text-off-white"><X size={14} /></button>
          </div>
        )}

        {/* Input */}
        <form onSubmit={handleSubmit} className="bg-[#181818] border border-[#282828] rounded-2xl px-3 py-3 sm:px-4 sm:py-4">
          <div className="flex items-end gap-2 sm:gap-3">
            {/* Botão de arquivo */}
            <button type="button" onClick={() => fileInputRef.current?.click()} className="shrink-0 h-11 w-11 flex items-center justify-center text-slate hover:text-[#1DB954] transition-colors" title="Anexar arquivo">
              <Paperclip size={20} />
            </button>
            <input ref={fileInputRef} type="file" accept=".pdf,.txt,.md,.png,.jpg,.jpeg,.webp" className="hidden"
              onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)} />

            <textarea ref={textareaRef} value={inputValue} onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); e.stopPropagation(); handleSendMessage(); } }}
              placeholder="Digite sua mensagem..." rows={1}
              className="w-full min-h-[44px] resize-none overflow-y-auto bg-transparent text-off-white placeholder:text-slate focus:outline-none text-sm sm:text-base leading-6 max-h-40" />

            {/* Botão parar / enviar */}
            {isTyping ? (
              <button type="button" onClick={handleStop} className="shrink-0 h-11 w-11 flex items-center justify-center bg-[#E91429] rounded-xl hover:brightness-110 transition-all" title="Parar geração">
                <Square size={16} className="text-white fill-white" />
              </button>
            ) : (
              <button type="submit" disabled={!inputValue.trim() && !selectedFile} className="shrink-0 h-11 bg-[#1DB954] text-black rounded-xl px-5 text-sm font-semibold hover:brightness-110 transition-all disabled:opacity-50">
                Enviar
              </button>
            )}
          </div>
        </form>

        {/* Barra inferior */}
        <div className="grid grid-cols-[1fr_auto_1fr] items-center mt-4 sm:mt-5 px-1 gap-3">
          <div className="flex items-center gap-1 sm:gap-2 justify-self-start">
            <button type="button" onClick={() => { const novo = conversationRating === 'positive' ? null : 'positive'; setConversationRating(novo); if (novo === 'positive') sendFeedback('like'); }} className={`p-2 rounded-lg transition-all duration-200 ${conversationRating === 'positive' ? 'bg-[#1ED76020] text-[#1ED760]' : 'text-slate hover:text-off-white'}`}><ThumbsUp size={18} /></button>
            <button type="button" onClick={() => { const novo = conversationRating === 'negative' ? null : 'negative'; setConversationRating(novo); if (novo === 'negative') sendFeedback('dislike'); }} className={`p-2 rounded-lg transition-all duration-200 ${conversationRating === 'negative' ? 'bg-[#E9142920] text-[#E91429]' : 'text-slate hover:text-off-white'}`}><ThumbsDown size={18} /></button>
            <button type="button" onClick={() => setShowCommands(true)} className="p-2 rounded-lg text-slate hover:text-off-white transition-colors" title="Comandos disponíveis"><Terminal size={18} /></button>
            <button type="button" onClick={() => setShowFeedback(true)} className="p-2 rounded-lg text-slate hover:text-off-white transition-colors"><Bug size={18} /></button>
            <div className="relative">
              <button type="button" onClick={() => setShowExportMenu((p) => !p)} className="p-2 rounded-lg text-slate hover:text-off-white transition-colors"><Download size={18} /></button>
              {showExportMenu && (
                <div className="absolute left-0 bottom-11 bg-[#282828] border border-[#3E3E3E] rounded-xl p-2 w-48 z-20">
                  <p className="text-xs text-slate px-2 py-1 mb-1">Exportar conversa</p>
                  {(['txt', 'json', 'md', 'pdf'] as const).map((fmt) => (
                    <button key={fmt} type="button" onClick={() => handleExport(fmt)} className="w-full text-left px-2 py-2 rounded-lg text-off-white text-sm hover:bg-[#3E3E3E] transition-colors">
                      Exportar como {fmt.toUpperCase()}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center justify-center gap-2 min-w-0 justify-self-center">
            <button type="button" onClick={handlePreviousConversation} disabled={!canNavigateConversations} className="p-1 text-slate hover:text-off-white transition-colors disabled:opacity-30"><ChevronLeft size={18} /></button>
            <button type="button" onClick={() => setShowHistory(true)} className="text-slate text-sm hover:text-off-white transition-colors font-body max-w-[220px] truncate text-center">{conversationTitle}</button>
            <button type="button" onClick={handleNextConversation} disabled={!canNavigateConversations} className="p-1 text-slate hover:text-off-white transition-colors disabled:opacity-30"><ChevronRight size={18} /></button>
          </div>

          {/* Toggle de provedor LLM */}
          <div className="flex items-center gap-2 justify-self-end">
            <button
              type="button"
              onClick={toggleProvider}
              disabled={providerLoading}
              className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors focus:outline-none ${llmProvider === 'ifes' ? 'bg-[#1DB954]' : 'bg-[#3E3E3E]'}`}
              title={`LLM: ${llmProvider === 'ifes' ? 'IFES Colatina (gemma3:12b)' : 'Local (qwen:4b)'}`}
            >
              <span className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${llmProvider === 'ifes' ? 'translate-x-6' : 'translate-x-1'}`} />
            </button>
            <span className="text-[10px] text-slate font-mono hidden sm:inline">
              {llmProvider === 'ifes' ? 'IFES' : 'Local'}
            </span>
            <button type="button" onClick={() => setShowSettings((p) => !p)}>
              <img src={userAvatar} alt={userAlt} className="w-9 h-9 rounded-full border-2 border-[#1DB954] hover:scale-105 transition-transform object-cover"
                onError={(e) => { (e.target as HTMLImageElement).src = `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(user?.name ?? 'U')}`; }} />
            </button>
            {showSettings && (
              <div className="absolute right-0 bottom-12 bg-[#282828] border border-[#3E3E3E] rounded-xl p-2 w-64 z-20">
                {isModerator && (
                  <button type="button" onClick={openDashboard} className="w-full flex items-center justify-between text-left px-3 py-2 rounded-lg hover:bg-[#3E3E3E] text-sm text-off-white">Dashboard <ExternalLink size={15} className="text-slate" /></button>
                )}
                {isModerator && (
                  <button type="button" onClick={openKnowledgeBase} className="w-full flex items-center justify-between text-left px-3 py-2 rounded-lg hover:bg-[#3E3E3E] text-sm text-off-white">Base de conhecimento <ExternalLink size={15} className="text-slate" /></button>
                )}
                <button type="button" onClick={openProfile} className="w-full flex items-center justify-between text-left px-3 py-2 rounded-lg hover:bg-[#3E3E3E] text-sm text-off-white">Perfil <UserCircle size={15} className="text-slate" /></button>
                <button type="button" onClick={() => { setShowSettings(false); setShowPreferences(true); }} className="w-full flex items-center justify-between text-left px-3 py-2 rounded-lg hover:bg-[#3E3E3E] text-sm text-off-white">Preferências <Settings size={15} className="text-slate" /></button>
                <button type="button" onClick={() => { setShowSettings(false); setShowFeedback(true); }} className="w-full flex items-center justify-between text-left px-3 py-2 rounded-lg hover:bg-[#3E3E3E] text-sm text-off-white">Feedback <MessageSquare size={15} className="text-slate" /></button>
                <button type="button" onClick={handleLogout} className="w-full text-left px-3 py-2 rounded-lg hover:bg-[#3E3E3E] text-sm text-[#E91429]">Sair</button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modais */}
      {showHistory && (
        <div className="fixed inset-0 bg-black/70 z-30 flex items-end sm:items-center justify-center p-4">
          <div className="bg-[#181818] border border-[#282828] rounded-2xl w-full max-w-lg p-4 sm:p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-off-white font-display text-lg">Histórico de conversas</h3>
              <button type="button" onClick={() => setShowHistory(false)} className="text-slate hover:text-off-white"><X size={18} /></button>
            </div>
            {historyContent}
            <button type="button" onClick={handleNewConversation} className="mt-4 w-full bg-[#1DB954] text-black rounded-xl py-2.5 text-sm font-semibold hover:brightness-110">Nova conversa</button>
          </div>
        </div>
      )}

      {showCommands && (
        <div className="fixed inset-0 bg-black/70 z-30 flex items-end sm:items-center justify-center p-4">
          <div className="bg-[#181818] border border-[#282828] rounded-2xl w-full max-w-xl p-4 sm:p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-off-white font-display text-lg flex items-center gap-2"><Terminal size={20} className="text-[#1DB954]" /> Comandos disponíveis</h3>
              <button type="button" onClick={() => setShowCommands(false)} className="text-slate hover:text-off-white"><X size={18} /></button>
            </div>
            <div className="space-y-1 max-h-80 overflow-auto">
              {COMMANDS.map((item, i) => (
                <div key={i} className="flex items-start gap-3 px-3 py-2.5 rounded-xl hover:bg-white/5 transition-colors">
                  <span className="text-[#1DB954] font-mono text-sm mt-0.5">▸</span>
                  <div>
                    <p className="text-off-white text-sm font-medium">{item.cmd}</p>
                    <p className="text-slate text-xs mt-0.5">Exemplo: <span className="text-off-white/70">{item.desc}</span></p>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 pt-3 border-t border-white/10">
              <p className="text-slate text-xs">💡 O MusicBot detecta automaticamente quando você quer usar o Spotify e executa a ação diretamente.</p>
            </div>
          </div>
        </div>
      )}

      {showFeedback && (
        <div className="fixed inset-0 bg-black/70 z-30 flex items-end sm:items-center justify-center p-4">
          <div className="bg-[#181818] border border-[#282828] rounded-2xl w-full max-w-lg p-4 sm:p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-off-white font-display text-lg">Enviar feedback</h3>
              <button type="button" onClick={() => setShowFeedback(false)} className="text-slate hover:text-off-white"><X size={18} /></button>
            </div>
            <textarea value={feedbackText} onChange={(e) => setFeedbackText(e.target.value)} placeholder="Descreva seu feedback..." className="w-full h-28 rounded-xl bg-white/5 border border-white/10 px-3 py-2 text-sm text-off-white placeholder:text-slate focus:outline-none" />
            <button type="button" onClick={() => { sendFeedback('report', feedbackText); setFeedbackText(''); setShowFeedback(false); }} className="mt-4 w-full bg-[#1DB954] text-black rounded-xl py-2.5 text-sm font-semibold hover:brightness-110">Enviar</button>
          </div>
        </div>
      )}

      {showPreferences && (
        <div className="fixed inset-0 bg-black/70 z-30 flex items-end sm:items-center justify-center p-4">
          <div className="bg-[#181818] border border-[#282828] rounded-2xl w-full max-w-md p-4 sm:p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-off-white font-display text-lg">Preferências</h3>
              <button type="button" onClick={() => setShowPreferences(false)} className="text-slate hover:text-off-white"><X size={18} /></button>
            </div>
            <div className="space-y-3">
              <label className="flex items-center justify-between rounded-xl bg-white/5 px-3 py-3"><span className="text-sm text-off-white">Habilitar áudio</span><input type="checkbox" checked={preferences.audioEnabled} onChange={(e) => setPreferences((p) => ({ ...p, audioEnabled: e.target.checked }))} /></label>
              <label className="flex items-center justify-between rounded-xl bg-white/5 px-3 py-3"><span className="text-sm text-off-white">Modo compacto</span><input type="checkbox" checked={preferences.compactMode} onChange={(e) => setPreferences((p) => ({ ...p, compactMode: e.target.checked }))} /></label>
            </div>
          </div>
        </div>
      )}

      {selectedSource && (
        <div className="fixed inset-0 bg-black/70 z-30 flex items-end sm:items-center justify-center p-4">
          <div className="bg-[#181818] border border-[#282828] rounded-2xl w-full max-w-xl p-4 sm:p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-off-white font-display text-lg">Fonte</h3>
              <button type="button" onClick={() => setSelectedSource(null)} className="text-slate hover:text-off-white"><X size={18} /></button>
            </div>
            <p className="text-off-white text-sm font-semibold">{selectedSource.name}</p>
            <p className="text-slate text-sm mt-1">{selectedSource.category} | {selectedSource.origin} | {selectedSource.date} | {selectedSource.version}</p>
            <p className="text-off-white text-sm mt-3 leading-relaxed">{selectedSource.excerpt}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chat;