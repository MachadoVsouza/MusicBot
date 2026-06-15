import { X } from 'lucide-react';

const PreferencesModal = ({
  preferences,
  onPreferencesChange,
  onClose,
}: {
  preferences: { audioEnabled: boolean; compactMode: boolean };
  onPreferencesChange: (prefs: { audioEnabled: boolean; compactMode: boolean }) => void;
  onClose: () => void;
}) => (
  <div className="fixed inset-0 bg-black/70 z-30 flex items-end sm:items-center justify-center p-4">
    <div className="bg-[#181818] border border-[#282828] rounded-2xl w-full max-w-md p-4 sm:p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-off-white font-display text-lg">Preferências</h3>
        <button type="button" onClick={onClose} className="text-slate hover:text-off-white"><X size={18} /></button>
      </div>
      <div className="space-y-3">
        <label className="flex items-center justify-between rounded-xl bg-white/5 px-3 py-3">
          <span className="text-sm text-off-white">Habilitar áudio</span>
          <input type="checkbox" checked={preferences.audioEnabled} onChange={(e) => onPreferencesChange({ ...preferences, audioEnabled: e.target.checked })} />
        </label>
        <label className="flex items-center justify-between rounded-xl bg-white/5 px-3 py-3">
          <span className="text-sm text-off-white">Modo compacto</span>
          <input type="checkbox" checked={preferences.compactMode} onChange={(e) => onPreferencesChange({ ...preferences, compactMode: e.target.checked })} />
        </label>
      </div>
    </div>
  </div>
);

export default PreferencesModal;