import { useEffect, useRef, useState } from 'react';
import { Music, Pause, Play } from 'lucide-react';
import type { Midia } from '@/types';

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

export default MiniPlayer;