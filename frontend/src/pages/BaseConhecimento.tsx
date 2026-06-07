import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Check,
  FileText,
  Loader2,
  Plus,
  Search,
  Trash2,
  X,
  AlertTriangle,
  ShieldOff,
} from 'lucide-react';
import { authFetch, useAuth } from '@/contexts/AuthContext';

const API = '/api';

interface Documento {
  id: number;
  titulo: string;
  tipo: string;
  status: 'pendente' | 'aprovado' | 'rejeitado';
  uploaded_by: string;
  uploaded_at: string;
  aprovado_por: string | null;
  aprovado_em: string | null;
  motivo_rejeicao: string | null;
}

const statusCfg = {
  pendente: { label: 'Pendente', color: '#F0A500', bg: 'rgba(240,165,0,0.15)' },
  aprovado: { label: 'Aprovado', color: '#1DB954', bg: 'rgba(29,185,84,0.15)' },
  rejeitado: { label: 'Rejeitado', color: '#E91429', bg: 'rgba(233,20,41,0.15)' },
};

function fmtDate(iso?: string) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('pt-BR');
}

const BaseConhecimento = () => {
  const navigate = useNavigate();
  const { user, isModerator } = useAuth();
  const [documentos, setDocumentos] = useState<Documento[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  // Modal de novo documento
  const [showModal, setShowModal] = useState(false);
  const [formTitulo, setFormTitulo] = useState('');
  const [formTipo, setFormTipo] = useState('txt');
  const [formConteudo, setFormConteudo] = useState('');
  const [formUrl, setFormUrl] = useState('');
  const [formArquivo, setFormArquivo] = useState<File | null>(null);
  const [formEnviando, setFormEnviando] = useState(false);
  const [formErro, setFormErro] = useState('');

  // Modal de rejeição
  const [rejeitarId, setRejeitarId] = useState<number | null>(null);
  const [rejeitarMotivo, setRejeitarMotivo] = useState('');

  const superUsuarioId = user?.superUsuarioId;

  const carregarDocs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterStatus) params.set('status', filterStatus);
      const res = await authFetch(`${API}/rag/documentos?${params}`);
      if (res.ok) {
        const data = await res.json();
        setDocumentos(data.data?.documentos ?? data.documentos ?? []);
      }
    } catch {
      /* falha silenciosa */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { carregarDocs(); }, [filterStatus]);

  // ── Submeter documento ────────────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormErro('');
    setFormEnviando(true);

    if (!superUsuarioId) {
      setFormErro('Você não tem permissão para enviar documentos. Apenas artistas/bandas (SuperUsuários) podem.');
      setFormEnviando(false);
      return;
    }

    try {
      if (formTipo === 'txt' && !formConteudo.trim()) {
        setFormErro('Preencha o conteúdo do texto');
        setFormEnviando(false);
        return;
      }
      if (formTipo === 'link' && !formUrl.trim()) {
        setFormErro('Preencha a URL');
        setFormEnviando(false);
        return;
      }

      const superId = String(superUsuarioId);

      if (formTipo === 'pdf' && formArquivo) {
        const fd = new FormData();
        fd.append('arquivo', formArquivo);
        fd.append('titulo', formTitulo || formArquivo.name);
        fd.append('super_usuario_id', superId);
        const r = await authFetch(`${API}/rag/documentos`, { method: 'POST', body: fd });
        if (r.ok) {
          setShowModal(false);
          resetForm();
          carregarDocs();
        } else {
          const d = await r.json();
          setFormErro(d.message || d.error || 'Erro ao enviar');
        }
        setFormEnviando(false);
        return;
      }

      const body: Record<string, unknown> = {
        titulo: formTitulo || 'Documento sem título',
        tipo: formTipo,
        super_usuario_id: superUsuarioId,
      };

      if (formTipo === 'txt') body.conteudo = formConteudo;
      if (formTipo === 'link') body.url = formUrl;

      const res = await authFetch(`${API}/rag/documentos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        setShowModal(false);
        resetForm();
        carregarDocs();
      } else {
        const d = await res.json();
        setFormErro(d.message || d.error || 'Erro ao enviar');
      }
    } catch {
      setFormErro('Erro de conexão');
    } finally {
      setFormEnviando(false);
    }
  };

  const resetForm = () => {
    setFormTitulo('');
    setFormTipo('txt');
    setFormConteudo('');
    setFormUrl('');
    setFormArquivo(null);
    setFormErro('');
  };

  // ── Aprovar / Rejeitar ────────────────────────────────────────────────────
  const handleAprovar = async (id: number) => {
    try {
      await authFetch(`${API}/rag/documentos/${id}/aprovar`, { method: 'POST' });
      carregarDocs();
    } catch {
      /* falha silenciosa */
    }
  };

  const handleRejeitar = async () => {
    if (!rejeitarId || !rejeitarMotivo.trim()) return;
    try {
      await authFetch(`${API}/rag/documentos/${rejeitarId}/rejeitar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ motivo: rejeitarMotivo }),
      });
      setRejeitarId(null);
      setRejeitarMotivo('');
      carregarDocs();
    } catch {
      /* falha silenciosa */
    }
  };

  const handleDeletar = async (id: number) => {
    try {
      await authFetch(`${API}/rag/documentos/${id}`, { method: 'DELETE' });
      carregarDocs();
    } catch {
      /* falha silenciosa */
    }
  };

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
            A Base de Conhecimento é exclusiva para artistas e bandas verificados no Spotify.
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

  // ── Render ────────────────────────────────────────────────────────────────
  const filtered = documentos.filter(d =>
    d.titulo.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-midnight p-4 md:p-8">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mx-auto max-w-7xl">
        <button onClick={() => navigate('/chat')} className="mb-6 flex items-center gap-1 text-sm text-slate hover:text-off-white transition-colors">
          <ArrowLeft size={16} /> Voltar ao chat
        </button>

        <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="font-display text-2xl font-bold text-off-white">Base de Conhecimento</h1>
              <span className="rounded-tag bg-[#1DB954] px-2 py-0.5 text-xs font-semibold text-black">Moderador</span>
            </div>
            <p className="text-sm text-slate">Gerencie documentos que alimentam o RAG. Aprovação necessária para indexar.</p>
          </div>
          <button onClick={() => { resetForm(); setShowModal(true); }} className="flex items-center gap-2 rounded-xl bg-[#1DB954] px-4 py-2.5 text-sm font-semibold text-white hover:brightness-110 transition-all">
            <Plus size={16} /> Novo Documento
          </button>
        </div>

        {/* Filtros */}
        <div className="mb-6 flex flex-wrap gap-3">
          <div className="bg-[#282828] border border-[#3E3E3E] flex min-w-[220px] flex-1 items-center gap-2 rounded-xl px-3">
            <Search size={16} className="text-slate" />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar por título..."
              className="flex-1 bg-transparent py-2.5 text-sm text-off-white placeholder:text-slate focus:outline-none" />
          </div>
          <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
            className="bg-[#282828] border border-[#3E3E3E] rounded-xl px-4 py-2.5 text-sm text-off-white focus:outline-none">
            <option value="">Todos os status</option>
            <option value="pendente">⏳ Pendente</option>
            <option value="aprovado">✅ Aprovado</option>
            <option value="rejeitado">❌ Rejeitado</option>
          </select>
        </div>

        {/* Tabela */}
        <div className="bg-[#181818] border border-[#282828] rounded-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#282828]">
                  <th className="p-4 text-left text-xs uppercase tracking-wider text-slate">Título</th>
                  <th className="p-4 text-left text-xs uppercase tracking-wider text-slate">Tipo</th>
                  <th className="p-4 text-left text-xs uppercase tracking-wider text-slate">Status</th>
                  <th className="hidden md:table-cell p-4 text-left text-xs uppercase tracking-wider text-slate">Enviado por</th>
                  <th className="hidden md:table-cell p-4 text-left text-xs uppercase tracking-wider text-slate">Data</th>
                  <th className="p-4 text-right text-xs uppercase tracking-wider text-slate">Ações</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={6} className="p-8 text-center"><Loader2 size={24} className="animate-spin text-[#1DB954] mx-auto" /></td></tr>
                ) : filtered.length === 0 ? (
                  <tr><td colSpan={6} className="p-8 text-center">
                    <p className="text-off-white font-semibold mb-1">Nenhum documento encontrado</p>
                    <p className="text-slate text-sm">Clique em "Novo Documento" para adicionar</p>
                  </td></tr>
                ) : filtered.map(doc => {
                  const st = statusCfg[doc.status];
                  return (
                    <tr key={doc.id} className="group border-b border-[#1E1E1E] hover:bg-[#282828] transition-colors">
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <FileText size={14} className="text-slate shrink-0" />
                          <span className="text-sm text-off-white truncate max-w-[200px]">{doc.titulo}</span>
                        </div>
                      </td>
                      <td className="p-4">
                        <span className="text-xs text-slate uppercase">{doc.tipo}</span>
                      </td>
                      <td className="p-4">
                        <span style={{ background: st.bg, color: st.color }}
                          className="inline-block px-2 py-0.5 rounded text-xs font-semibold">
                          {st.label}
                        </span>
                      </td>
                      <td className="hidden md:table-cell p-4 text-sm text-slate">{doc.uploaded_by?.slice(0, 12)}...</td>
                      <td className="hidden md:table-cell p-4 text-sm text-slate">{fmtDate(doc.uploaded_at)}</td>
                      <td className="p-4 text-right">
                        <div className="flex items-center justify-end gap-1">
                          {doc.status === 'pendente' && (
                            <>
                              <button onClick={() => handleAprovar(doc.id)}
                                className="rounded-lg p-1.5 text-[#1DB954] hover:bg-[rgba(29,185,84,0.15)] transition-colors" title="Aprovar">
                                <Check size={14} />
                              </button>
                              <button onClick={() => setRejeitarId(doc.id)}
                                className="rounded-lg p-1.5 text-[#E91429] hover:bg-[rgba(233,20,41,0.15)] transition-colors" title="Rejeitar">
                                <X size={14} />
                              </button>
                            </>
                          )}
                          {doc.status === 'rejeitado' && doc.motivo_rejeicao && (
                            <span className="text-xs text-slate italic truncate max-w-[100px]" title={doc.motivo_rejeicao}>
                              {doc.motivo_rejeicao}
                            </span>
                          )}
                          <button onClick={() => handleDeletar(doc.id)}
                            className="rounded-lg p-1.5 text-slate hover:text-[#E91429] transition-colors opacity-0 group-hover:opacity-100" title="Excluir">
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </motion.div>

      {/* Modal de novo documento */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={() => setShowModal(false)}>
          <div className="absolute inset-0 bg-black/75" />
          <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }}
            onClick={e => e.stopPropagation()}
            className="bg-[#181818] border border-[#282828] relative z-10 w-full max-w-[560px] rounded-modal p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="font-display text-xl font-bold text-off-white">Novo Documento</h2>
                <p className="text-sm text-slate mt-1">O conteúdo será extraído e indexado após aprovação</p>
              </div>
              <button onClick={() => setShowModal(false)} className="text-slate hover:text-off-white"><X size={20} /></button>
            </div>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <input value={formTitulo} onChange={e => setFormTitulo(e.target.value)} placeholder="Título do documento"
                className="w-full rounded-xl bg-[#282828] border border-[#3E3E3E] px-4 py-3 text-sm text-off-white placeholder:text-slate focus:outline-none" />

              <select value={formTipo} onChange={e => setFormTipo(e.target.value)}
                className="w-full rounded-xl bg-[#282828] border border-[#3E3E3E] px-4 py-3 text-sm text-off-white focus:outline-none">
                <option value="txt">Texto</option>
                <option value="link">Link (URL)</option>
                <option value="pdf">PDF</option>
              </select>

              {formTipo === 'txt' && (
                <textarea value={formConteudo} onChange={e => setFormConteudo(e.target.value)} rows={5} placeholder="Conteúdo do documento..."
                  className="w-full resize-none rounded-xl bg-[#282828] border border-[#3E3E3E] px-4 py-3 text-sm text-off-white placeholder:text-slate focus:outline-none" />
              )}

              {formTipo === 'link' && (
                <input value={formUrl} onChange={e => setFormUrl(e.target.value)} placeholder="https://..."
                  className="w-full rounded-xl bg-[#282828] border border-[#3E3E3E] px-4 py-3 text-sm text-off-white placeholder:text-slate focus:outline-none" />
              )}

              {formTipo === 'pdf' && (
                <input type="file" accept=".pdf" onChange={e => setFormArquivo(e.target.files?.[0] ?? null)}
                  className="w-full text-sm text-slate file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:bg-[#1DB954] file:text-black file:font-semibold file:text-sm" />
              )}

              {formErro && <p className="text-[#E91429] text-sm flex items-center gap-1"><AlertTriangle size={14} /> {formErro}</p>}

              <div className="flex gap-3">
                <button type="button" onClick={() => setShowModal(false)}
                  className="flex-1 rounded-xl bg-[#282828] border border-[#3E3E3E] py-3 text-sm text-slate hover:text-off-white transition-colors">Cancelar</button>
                <button type="submit" disabled={formEnviando}
                  className="flex-1 rounded-xl bg-[#1DB954] py-3 text-sm font-semibold text-white hover:brightness-110 transition-all disabled:opacity-50 flex items-center justify-center gap-2">
                  {formEnviando && <Loader2 size={14} className="animate-spin" />}
                  Enviar para aprovação
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}

      {/* Modal de rejeição */}
      {rejeitarId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={() => setRejeitarId(null)}>
          <div className="absolute inset-0 bg-black/75" />
          <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }}
            onClick={e => e.stopPropagation()}
            className="bg-[#181818] border border-[#282828] relative z-10 w-full max-w-md rounded-modal p-6">
            <h3 className="font-display text-lg font-bold text-off-white mb-3">Rejeitar Documento</h3>
            <textarea value={rejeitarMotivo} onChange={e => setRejeitarMotivo(e.target.value)} rows={3} placeholder="Motivo da rejeição..."
              className="w-full resize-none rounded-xl bg-[#282828] border border-[#3E3E3E] px-4 py-3 text-sm text-off-white placeholder:text-slate focus:outline-none mb-4" />
            <div className="flex gap-3">
              <button onClick={() => setRejeitarId(null)}
                className="flex-1 rounded-xl bg-[#282828] border border-[#3E3E3E] py-3 text-sm text-slate hover:text-off-white">Cancelar</button>
              <button onClick={handleRejeitar} disabled={!rejeitarMotivo.trim()}
                className="flex-1 rounded-xl bg-[#E91429] py-3 text-sm font-semibold text-white hover:brightness-110 disabled:opacity-50">Rejeitar</button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default BaseConhecimento;