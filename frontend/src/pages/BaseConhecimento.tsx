import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import type { LucideIcon } from 'lucide-react';
import {
  ArrowLeft,
  ClipboardList,
  Database,
  FileText,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  X,
} from 'lucide-react';

type KnowledgeDocType = 'document' | 'api' | 'record';

interface KnowledgeDoc {
  id: string;
  type: KnowledgeDocType;
  title: string;
  category: string;
  origin: string;
  date: string;
  version: string;
}

interface KnowledgeFormState {
  title: string;
  type: KnowledgeDocType;
  category: string;
  origin: string;
  version: string;
  reference: string;
  content: string;
}

const knowledgeDocs: KnowledgeDoc[] = [];

const categoryOptions = [
  'Artistas',
  'Albuns',
  'Playlists',
  'Generos',
  'Curiosidades',
  'Integracoes',
];

const originOptions = [
  'PDF',
  'Spotify API',
  'ReccoBeats API',
  'Documento manual',
  'Link externo',
];

const typeConfig: Record<
  KnowledgeDocType,
  { label: string; icon: LucideIcon; className: string }
> = {
  document: { label: 'Documento', icon: FileText, className: 'text-[#1ED760]' },
  api: { label: 'API', icon: Database, className: 'text-white' },
  record: { label: 'Registro', icon: ClipboardList, className: 'text-[#B3B3B3]' },
};

const initialFormState: KnowledgeFormState = {
  title: '',
  type: 'document',
  category: '',
  origin: '',
  version: '',
  reference: '',
  content: '',
};

const BaseConhecimento = () => {
  const navigate = useNavigate();
  const [docs] = useState<KnowledgeDoc[]>(knowledgeDocs);
  const [search, setSearch] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [filterOrigin, setFilterOrigin] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<KnowledgeFormState>(initialFormState);

  const filteredDocs = useMemo(
    () =>
      docs.filter((doc) => {
        const matchesSearch = doc.title.toLowerCase().includes(search.toLowerCase());
        const matchesCategory = !filterCategory || doc.category === filterCategory;
        const matchesOrigin = !filterOrigin || doc.origin === filterOrigin;

        return matchesSearch && matchesCategory && matchesOrigin;
      }),
    [docs, search, filterCategory, filterOrigin],
  );

  const closeModal = () => {
    setShowModal(false);
    setForm(initialFormState);
  };

  const openModal = () => {
    setShowModal(true);
  };

  const updateForm = <K extends keyof KnowledgeFormState>(key: K, value: KnowledgeFormState[K]) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  return (
    <div className="min-h-screen bg-midnight music-texture p-4 md:p-8">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="mx-auto max-w-7xl"
      >
        <button
          onClick={() => navigate('/chat')}
          className="mb-6 flex items-center gap-1 text-sm font-body text-slate transition-colors hover:text-off-white"
        >
          <ArrowLeft size={16} />
          Voltar ao chat
        </button>

        <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <h1 className="font-display text-2xl font-bold text-off-white">
                Base de Conhecimento
              </h1>
              <span className="rounded-tag bg-[#1DB954] px-2 py-0.5 text-xs font-mono-label font-semibold text-black">
                Moderador
              </span>
            </div>

            <p className="max-w-3xl text-sm font-body leading-6 text-slate">
              Biblioteca administrativa do MusicBot. Aqui o moderador organiza documentos,
              referencias e integracoes que alimentam as respostas do chatbot.
            </p>
          </div>

          <button
            onClick={openModal}
            className="flex w-fit items-center gap-2 rounded-xl bg-[#1DB954] px-4 py-2.5 text-sm font-body font-semibold text-off-white transition-all duration-200 hover:brightness-110"
          >
            <Plus size={16} />
            Cadastrar novo documento
          </button>
        </div>

        <div className="mb-6 flex flex-wrap gap-3">
          <div className="bg-[#282828] border border-[#3E3E3E] flex min-w-[220px] flex-1 items-center gap-2 rounded-xl px-3">
            <Search size={16} className="text-slate" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Buscar por titulo..."
              className="flex-1 bg-transparent py-2.5 text-sm font-body text-off-white placeholder:text-slate focus:outline-none"
            />
          </div>

          <select
            value={filterCategory}
            onChange={(event) => setFilterCategory(event.target.value)}
            className="bg-[#282828] border border-[#3E3E3E] min-w-[180px] rounded-xl px-4 py-2.5 text-sm font-body text-off-white focus:outline-none"
          >
            <option value="" className="bg-midnight text-off-white">
              Todas categorias
            </option>
            {categoryOptions.map((category) => (
              <option key={category} value={category} className="bg-midnight text-off-white">
                {category}
              </option>
            ))}
          </select>

          <select
            value={filterOrigin}
            onChange={(event) => setFilterOrigin(event.target.value)}
            className="bg-[#282828] border border-[#3E3E3E] min-w-[180px] rounded-xl px-4 py-2.5 text-sm font-body text-off-white focus:outline-none"
          >
            <option value="" className="bg-midnight text-off-white">
              Todas origens
            </option>
            {originOptions.map((origin) => (
              <option key={origin} value={origin} className="bg-midnight text-off-white">
                {origin}
              </option>
            ))}
          </select>
        </div>

        <div className="bg-[#181818] border border-[#282828] overflow-hidden rounded-card">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#282828]">
                  <th className="p-4 text-left text-xs font-mono-label uppercase tracking-wider text-slate">
                    Tipo
                  </th>
                  <th className="p-4 text-left text-xs font-mono-label uppercase tracking-wider text-slate">
                    Titulo
                  </th>
                  <th className="hidden p-4 text-left text-xs font-mono-label uppercase tracking-wider text-slate md:table-cell">
                    Categoria
                  </th>
                  <th className="hidden p-4 text-left text-xs font-mono-label uppercase tracking-wider text-slate md:table-cell">
                    Origem
                  </th>
                  <th className="hidden p-4 text-left text-xs font-mono-label uppercase tracking-wider text-slate lg:table-cell">
                    Data
                  </th>
                  <th className="hidden p-4 text-left text-xs font-mono-label uppercase tracking-wider text-slate lg:table-cell">
                    Versao
                  </th>
                  <th className="p-4 text-right text-xs font-mono-label uppercase tracking-wider text-slate">
                    Acoes
                  </th>
                </tr>
              </thead>

              <tbody>
                {filteredDocs.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8">
                      <div className="rounded-card border border-dashed border-[#282828] bg-[#0D0D0D] px-4 py-10 text-center">
                        <p className="font-display text-lg font-semibold text-off-white">
                          Nenhum documento encontrado
                        </p>
                        <p className="mx-auto mt-2 max-w-2xl text-sm font-body leading-6 text-slate">
                          A estrutura da tabela ja esta pronta para listar documentos, APIs e
                          registros assim que os dados passarem a vir do banco.
                        </p>
                        <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
                          <ActionIconButton icon={Pencil} label="Editar" disabled />
                          <ActionIconButton icon={RefreshCw} label="Atualizar" disabled />
                          <ActionIconButton icon={Trash2} label="Excluir" disabled />
                        </div>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredDocs.map((doc) => {
                    const config = typeConfig[doc.type];
                    const TypeIcon = config.icon;

                    return (
                      <tr
                        key={doc.id}
                        className="group border-b border-[#1E1E1E] transition-colors hover:bg-[#282828]"
                      >
                        <td className="p-4">
                          <span className={`flex items-center gap-2 text-sm font-body ${config.className}`}>
                            <TypeIcon size={16} />
                            {config.label}
                          </span>
                        </td>
                        <td className="p-4 text-sm font-body text-off-white">{doc.title}</td>
                        <td className="hidden p-4 text-sm font-body text-slate md:table-cell">
                          {doc.category}
                        </td>
                        <td className="hidden p-4 text-sm font-body text-slate md:table-cell">
                          {doc.origin}
                        </td>
                        <td className="hidden p-4 text-xs font-mono-label text-slate lg:table-cell">
                          {doc.date}
                        </td>
                        <td className="hidden p-4 text-xs font-mono-label text-teal lg:table-cell">
                          {doc.version}
                        </td>
                        <td className="p-4">
                          <div className="flex items-center justify-end gap-1 opacity-100 transition-opacity md:opacity-0 md:group-hover:opacity-100">
                            <ActionIconButton icon={Pencil} label="Editar" />
                            <ActionIconButton icon={RefreshCw} label="Atualizar" />
                            <ActionIconButton icon={Trash2} label="Excluir" />
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </motion.div>

      {showModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          onClick={closeModal}
        >
          <div className="absolute inset-0 bg-black/75" />

          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2 }}
            onClick={(event) => event.stopPropagation()}
            className="bg-[#181818] border border-[#282828] relative z-10 w-full max-w-[560px] rounded-modal p-6"
          >
            <div className="mb-6 flex items-center justify-between gap-4">
              <div>
                <h2 className="font-display text-xl font-bold text-off-white">
                  Cadastrar Documento
                </h2>
                <p className="mt-1 text-sm font-body text-slate">
                  Interface pronta para documentos, PDFs, links e integracoes.
                </p>
              </div>

              <button
                onClick={closeModal}
                className="text-gray-light transition-colors hover:text-off-white"
              >
                <X size={20} />
              </button>
            </div>

            <form
              className="flex flex-col gap-4"
              onSubmit={(event) => {
                event.preventDefault();
                closeModal();
              }}
            >
              <input
                value={form.title}
                onChange={(event) => updateForm('title', event.target.value)}
                placeholder="Titulo do documento"
                className="w-full rounded-xl bg-[#282828] border border-[#3E3E3E] px-4 py-3 text-sm font-body text-off-white placeholder:text-slate focus:outline-none"
              />

              <div className="grid gap-4 md:grid-cols-2">
                <select
                  value={form.type}
                  onChange={(event) => updateForm('type', event.target.value as KnowledgeDocType)}
                  className="w-full rounded-xl bg-[#282828] border border-[#3E3E3E] px-4 py-3 text-sm font-body text-off-white focus:outline-none"
                >
                  <option value="document" className="bg-midnight text-off-white">
                    Documento
                  </option>
                  <option value="api" className="bg-midnight text-off-white">
                    API
                  </option>
                  <option value="record" className="bg-midnight text-off-white">
                    Registro
                  </option>
                </select>

                <input
                  value={form.version}
                  onChange={(event) => updateForm('version', event.target.value)}
                  placeholder="Versao"
                  className="w-full rounded-xl bg-[#282828] border border-[#3E3E3E] px-4 py-3 text-sm font-body text-off-white placeholder:text-slate focus:outline-none"
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <select
                  value={form.category}
                  onChange={(event) => updateForm('category', event.target.value)}
                  className="w-full rounded-xl bg-[#282828] border border-[#3E3E3E] px-4 py-3 text-sm font-body text-off-white focus:outline-none"
                >
                  <option value="" className="bg-midnight text-off-white">
                    Categoria
                  </option>
                  {categoryOptions.map((category) => (
                    <option key={category} value={category} className="bg-midnight text-off-white">
                      {category}
                    </option>
                  ))}
                </select>

                <select
                  value={form.origin}
                  onChange={(event) => updateForm('origin', event.target.value)}
                  className="w-full rounded-xl bg-[#282828] border border-[#3E3E3E] px-4 py-3 text-sm font-body text-off-white focus:outline-none"
                >
                  <option value="" className="bg-midnight text-off-white">
                    Origem
                  </option>
                  {originOptions.map((origin) => (
                    <option key={origin} value={origin} className="bg-midnight text-off-white">
                      {origin}
                    </option>
                  ))}
                </select>
              </div>

              <input
                value={form.reference}
                onChange={(event) => updateForm('reference', event.target.value)}
                placeholder="Arquivo, endpoint ou link de referencia"
                className="w-full rounded-xl bg-[#282828] border border-[#3E3E3E] px-4 py-3 text-sm font-body text-off-white placeholder:text-slate focus:outline-none"
              />

              <textarea
                value={form.content}
                onChange={(event) => updateForm('content', event.target.value)}
                rows={5}
                placeholder="Resumo, contexto ou conteudo base do documento"
                className="w-full resize-none rounded-xl bg-[#282828] border border-[#3E3E3E] px-4 py-3 text-sm font-body text-off-white placeholder:text-slate focus:outline-none"
              />

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={closeModal}
                  className="flex-1 rounded-xl bg-[#282828] border border-[#3E3E3E] py-3 text-sm font-body text-gray-light transition-colors hover:text-off-white"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="flex-1 rounded-xl bg-[#1DB954] py-3 text-sm font-body font-semibold text-off-white transition-all hover:brightness-110"
                >
                  Salvar documento
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
};

const ActionIconButton = ({
  icon: Icon,
  label,
  disabled = false,
}: {
  icon: LucideIcon;
  label: string;
  disabled?: boolean;
}) => (
  <button
    type="button"
    disabled={disabled}
    title={label}
    className="rounded-lg p-1.5 text-slate transition-colors hover:bg-[hsla(0,0%,100%,0.06)] hover:text-off-white disabled:cursor-default disabled:opacity-60"
  >
    <Icon size={14} />
  </button>
);

export default BaseConhecimento;
