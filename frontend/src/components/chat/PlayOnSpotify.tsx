import { useState } from "react";
import { ExternalLink, Play } from "lucide-react";
import { authFetch } from "@/contexts/AuthContext";
import type { Track } from "@/types";

const API = "/api";

const PlayOnSpotify = ({
  track,
  selectedDeviceId,
}: {
  track: Track;
  selectedDeviceId: string | null;
}) => {
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const handlePlay = async () => {
    setLoading(true);
    setMsg(null);
    try {
      const res = await authFetch(
        `${API}/spotify/search-track?q=${encodeURIComponent(`${track.name} ${track.artist}`)}`
      );
      if (!res.ok) {
        setMsg("❌ Não foi possível tocar");
        setLoading(false);
        return;
      }
      const data = await res.json();
      const trackData = data.data?.track ?? data.track;
      if (!trackData?.uri) {
        setMsg("❌ Música não encontrada no Spotify");
        setLoading(false);
        return;
      }

      const playRes = await authFetch(`${API}/spotify/play`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          track_uri: trackData.uri,
          device_id: selectedDeviceId || undefined,
        }),
      });
      const playData = await playRes.json();
      const playResult = playData.data ?? playData;
      setMsg(playResult.mensagem || playResult.erro || "✅ Tocando!");
    } catch {
      setMsg("❌ Erro ao tentar tocar");
    } finally {
      setLoading(false);
      setTimeout(() => setMsg(null), 3000);
    }
  };

  return (
    <div className="flex items-center gap-1.5">
      <button
        type="button"
        onClick={handlePlay}
        disabled={loading}
        className="w-7 h-7 rounded-full bg-[#1DB954] flex items-center justify-center text-black disabled:opacity-50 transition-all hover:brightness-110"
        title="Tocar no Spotify"
      >
        {loading ? (
          <span className="text-[10px]">...</span>
        ) : (
          <Play size={12} />
        )}
      </button>
      {track.spotify_url && (
        <a
          href={track.spotify_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-gray-400 hover:text-[#1DB954] transition-colors flex items-center"
          title="Abrir no Spotify"
        >
          <ExternalLink size={12} />
        </a>
      )}
      {msg && (
        <span
          className={`text-[10px] whitespace-nowrap ${
            msg.includes("❌") ? "text-[#E91429]" : "text-[#1DB954]"
          }`}
        >
          {msg}
        </span>
      )}
    </div>
  );
};

export default PlayOnSpotify;