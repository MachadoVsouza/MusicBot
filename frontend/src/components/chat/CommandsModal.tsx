import { X, Terminal } from 'lucide-react';

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

const CommandsModal = ({ onClose }: { onClose: () => void }) => (
  <div className="fixed inset-0 bg-black/70 z-30 flex items-end sm:items-center justify-center p-4">
    <div className="bg-[#181818] border border-[#282828] rounded-2xl w-full max-w-xl p-4 sm:p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-off-white font-display text-lg flex items-center gap-2"><Terminal size={20} className="text-[#1DB954]" /> Comandos disponíveis</h3>
        <button type="button" onClick={onClose} className="text-slate hover:text-off-white"><X size={18} /></button>
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
);

export default CommandsModal;