const ExportMenu = ({
  onExport,
}: {
  onExport: (format: 'txt' | 'json' | 'md' | 'pdf') => void;
}) => (
  <div className="absolute left-0 bottom-11 bg-[#282828] border border-[#3E3E3E] rounded-xl p-2 w-48 z-20">
    <p className="text-xs text-slate px-2 py-1 mb-1">Exportar conversa</p>
    {(['txt', 'json', 'md', 'pdf'] as const).map((fmt) => (
      <button key={fmt} type="button" onClick={() => onExport(fmt)} className="w-full text-left px-2 py-2 rounded-lg text-off-white text-sm hover:bg-[#3E3E3E] transition-colors">
        Exportar como {fmt.toUpperCase()}
      </button>
    ))}
  </div>
);

export default ExportMenu;