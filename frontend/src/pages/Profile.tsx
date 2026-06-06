import { useEffect, useState } from "react";
import { authFetch } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { ExternalLink, Play, Smartphone, Monitor, Speaker, ChevronDown } from "lucide-react";

const API = "/api";

interface UserProfile {
  name: string;
  email: string;
  avatar: string;
  plan: string;
  followers: number;
}

interface Track {
  name: string;
  artist: string;
  album: string;
  played_at: string;
  preview_url: string | null;
  spotify_url: string | null;
}

function timeAgo(dateStr: string): string {
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (diff < 60) return "agora";
  if (diff < 3600) return `${Math.floor(diff / 60)}min`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
  return `${Math.floor(diff / 86400)}d`;
}

// ── Botão "Tocar no Spotify" ──────────────────────────────────────────────────
interface Device {
  id: string;
  name: string;
  type: string;
  is_active: boolean;
}

const deviceIcon = (type: string) => {
  switch (type.toLowerCase()) {
    case "smartphone": return <Smartphone size={12} />;
    case "computer": return <Monitor size={12} />;
    case "speaker": return <Speaker size={12} />;
    default: return <Monitor size={12} />;
  }
};

const PlayOnSpotify = ({ track, devices, selectedDeviceId, onSelectDevice }: { track: Track; devices: Device[]; selectedDeviceId: string | null; onSelectDevice: (id: string | null) => void }) => {
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const handlePlay = async () => {
    setLoading(true);
    setMsg(null);
    try {
      const res = await authFetch(`${API}/spotify/search-track?q=${encodeURIComponent(`${track.name} ${track.artist}`)}`);
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
        body: JSON.stringify({ track_uri: trackData.uri, device_id: selectedDeviceId || undefined }),
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
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <button
        type="button"
        onClick={handlePlay}
        disabled={loading}
        style={{
          ...styles.previewBtn,
          opacity: loading ? 0.5 : 1,
          cursor: loading ? "not-allowed" : "pointer",
        }}
        title="Tocar no Spotify"
      >
        {loading ? <span style={{ fontSize: 10 }}>...</span> : <Play size={12} />}
      </button>
      {track.spotify_url && (
        <a
          href={track.spotify_url}
          target="_blank"
          rel="noopener noreferrer"
          style={styles.spotifyLink}
          title="Abrir no Spotify"
        >
          <ExternalLink size={12} />
        </a>
      )}
      {msg && <span style={{ fontSize: 10, color: msg.includes("❌") ? "#E91429" : "#1DB954", whiteSpace: "nowrap" }}>{msg}</span>}
    </div>
  );
};

export default function Profile() {
  const navigate = useNavigate();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
  const [showDevicePicker, setShowDevicePicker] = useState(false);
  const [loading, setLoading] = useState(true);
  const [hoveredTrack, setHoveredTrack] = useState<number | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [profileRes, tracksRes, devicesRes] = await Promise.all([
          authFetch(`${API}/spotify/profile`),
          authFetch(`${API}/spotify/recently-played`),
          authFetch(`${API}/spotify/devices`),
        ]);

        if (devicesRes.ok) {
          const devicesData = await devicesRes.json();
          const d = devicesData.data?.devices ?? devicesData.devices ?? [];
          setDevices(d);
          const active = d.find((dev: Device) => dev.is_active);
          setSelectedDeviceId(active?.id ?? null);
        }

        if (!profileRes.ok) {
          navigate("/chat");
          return;
        }

        const profileJson = await profileRes.json();
        const profileData = profileJson.data ?? profileJson;
        setUser({
          name: profileData.display_name ?? profileData.name ?? "",
          email: profileData.email ?? "",
          avatar: 'https://api.dicebear.com/7.x/initials/svg?seed=user',
          plan: profileData.plan ?? "FREE",
          followers: profileData.followers ?? 0,
        });

        if (tracksRes.ok) {
          const tracksData = await tracksRes.json();
          setTracks(tracksData.tracks ?? []);
        }
      } catch {
        navigate("/chat");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [navigate]);

  async function handleLogout() {
    await fetch(`${API}/auth/logout`, { method: "POST" });
    navigate("/login");
  }

  if (loading) {
    return (
      <div style={styles.loadingWrap}>
        <div style={styles.waveWrap}>
          {[12, 28, 18, 38, 22, 32, 14, 24, 36, 16].map((h, i) => (
            <span key={i} style={{ ...styles.bar, height: h, animationDelay: `${i * 0.07}s` }} />
          ))}
        </div>
        <p style={styles.loadingText}>Carregando seu universo musical...</p>
        <style>{waveAnim}</style>
      </div>
    );
  }

  if (!user) return null;

  const initials = user.name.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase();

  return (
    <div style={styles.page}>
      <style>{waveAnim + scrollAnim + glowAnim}</style>
      <div style={styles.bgGradient} />

      <header style={styles.header}>
        <div style={styles.logo}>
          <span style={styles.logoIcon}>♪</span>
          <span style={styles.brand}>MUSICBOT</span>
        </div>
        <button style={styles.logoutBtn} onClick={handleLogout}>
          <span>→</span> Sair
        </button>
      </header>

      <main style={styles.main}>
        <div style={styles.profileCard}>
          <div style={styles.banner}><div style={styles.bannerOverlay} /></div>
          <div style={styles.avatarRow}>
            {user.avatar ? (
              <img src={user.avatar} alt={user.name} style={styles.avatar} />
            ) : (
              <div style={styles.avatarPlaceholder}>{initials}</div>
            )}
            <div style={styles.statusBadge}>
              <span style={styles.statusDot} />
              <span>Ativo</span>
            </div>
          </div>
          <div style={styles.userInfo}>
            <h1 style={styles.userName}>{user.name}</h1>
            <p style={styles.userEmail}>{user.email}</p>
            <div style={styles.divider} />
            <div style={styles.statsRow}>
              <div style={styles.statBox}>
                <span style={styles.statValue}>{user.followers.toLocaleString("pt-BR")}</span>
                <span style={styles.statLabel}><span style={styles.statIcon}>👥</span> Seguidores</span>
              </div>
              <div style={styles.statBox}>
                <span style={styles.statValue}>{user.plan}</span>
                <span style={styles.statLabel}><span style={styles.statIcon}>⭐</span> Plano</span>
              </div>
            </div>
          </div>
        </div>

        <div style={styles.tracksSection}>
          <div style={styles.sectionHeader}>
            <div style={styles.waveSmall}>
              {[8, 16, 10, 20, 12, 18, 14].map((h, i) => (
                <span key={i} style={{ ...styles.barSmall, height: h, animationDelay: `${i * 0.1}s` }} />
              ))}
            </div>
            <div>
              <h2 style={styles.sectionTitle}>Ouvidas recentemente</h2>
              <p style={styles.sectionSubtitle}>Suas últimas faixas no Spotify</p>
            </div>
          </div>

          <div style={styles.trackList}>
            {tracks.length === 0 ? (
              <div style={styles.emptyState}>
                <div style={styles.emptyIcon}>🎧</div>
                <p style={styles.emptyMsg}>Nenhuma música encontrada.</p>
                <p style={styles.emptySub}>Ouça algo no Spotify para aparecer aqui</p>
              </div>
            ) : (
              <>
                {/* Seletor de dispositivo */}
                {devices.length > 0 && (
                  <div style={{ padding: "8px 28px", borderBottom: "1px solid rgba(255,255,255,0.03)", display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" as const }}>
                    <span style={{ fontSize: 11, color: "#888" }}>▶ Tocando em:</span>
                    <div style={{ position: "relative" as const }}>
                      <button
                        type="button"
                        onClick={() => setShowDevicePicker(!showDevicePicker)}
                        style={{
                          background: "rgba(255,255,255,0.05)",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: 8,
                          color: "#e8e8e8",
                          fontSize: 12,
                          padding: "6px 12px",
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center",
                          gap: 6,
                        }}
                      >
                        {deviceIcon(devices.find(d => d.id === selectedDeviceId)?.type || "computer")}
                        {selectedDeviceId ? devices.find(d => d.id === selectedDeviceId)?.name || "Selecionar" : "Dispositivo ativo"}
                        <ChevronDown size={12} />
                      </button>
                      {showDevicePicker && (
                        <div style={{
                          position: "absolute",
                          top: "100%",
                          left: 0,
                          marginTop: 4,
                          background: "#1a1a1a",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: 8,
                          padding: 4,
                          zIndex: 20,
                          minWidth: 180,
                        }}>
                          <div style={{ fontSize: 10, color: "#888", padding: "6px 8px", textTransform: "uppercase", letterSpacing: "0.05em" }}>Dispositivos</div>
                          {devices.map(dev => (
                            <button
                              key={dev.id}
                              type="button"
                              onClick={() => { setSelectedDeviceId(dev.id); setShowDevicePicker(false); }}
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 8,
                                width: "100%",
                                background: dev.id === selectedDeviceId ? "rgba(29,185,84,0.15)" : "transparent",
                                border: "none",
                                borderRadius: 6,
                                padding: "8px 10px",
                                color: dev.id === selectedDeviceId ? "#1DB954" : "#e8e8e8",
                                fontSize: 12,
                                cursor: "pointer",
                                textAlign: "left" as const,
                              }}
                            >
                              {deviceIcon(dev.type)}
                              <span style={{ flex: 1 }}>{dev.name}</span>
                              {dev.is_active && <span style={{ fontSize: 10, color: "#1DB954" }}>ativo</span>}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {tracks.map((track, i) => (
                  <div
                    key={i}
                    style={{ ...styles.trackRow, ...(hoveredTrack === i ? styles.trackRowHover : {}) }}
                    onMouseEnter={() => setHoveredTrack(i)}
                    onMouseLeave={() => setHoveredTrack(null)}
                  >
                    <div style={styles.trackNumber}>
                      <span style={styles.trackIndex}>{String(i + 1).padStart(2, "0")}</span>
                      {hoveredTrack === i && <span style={styles.playIcon}>▶</span>}
                    </div>
                    <div style={styles.trackInfo}>
                      <span style={styles.trackName}>{track.name}</span>
                      <span style={styles.trackArtist}>{track.artist} · {track.album}</span>
                    </div>
                    <div style={styles.trackMeta}>
                      <PlayOnSpotify track={track} devices={devices} selectedDeviceId={selectedDeviceId} onSelectDevice={setSelectedDeviceId} />
                      <span style={styles.trackTime}>
                        <span style={styles.clockIcon}>🕐</span> {timeAgo(track.played_at)}
                      </span>
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  page: { background: "#0a0a0a", minHeight: "100vh", fontFamily: "'Inter', sans-serif", color: "#e8e8e8", position: "relative", overflowX: "hidden" },
  bgGradient: { position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "radial-gradient(circle at 20% 50%, rgba(29,185,84,0.08) 0%, transparent 50%)", pointerEvents: "none", zIndex: 0 },
  header: { position: "relative", zIndex: 10, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "20px 48px", borderBottom: "1px solid rgba(255,255,255,0.05)", backdropFilter: "blur(10px)", background: "rgba(10,10,10,0.8)" },
  logo: { display: "flex", alignItems: "center", gap: 10 },
  logoIcon: { fontSize: 28, color: "#1DB954", fontWeight: 400 },
  brand: { fontFamily: "'Inter', sans-serif", fontSize: 18, fontWeight: 700, letterSpacing: "-0.02em", background: "linear-gradient(135deg, #fff 0%, #1DB954 100%)", backgroundClip: "text", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" },
  logoutBtn: { background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.1)", color: "#e8e8e8", fontFamily: "'Inter', sans-serif", fontSize: 13, fontWeight: 500, padding: "8px 20px", borderRadius: 8, cursor: "pointer", display: "flex", alignItems: "center", gap: 8, transition: "all 0.2s ease" },
  main: { position: "relative", zIndex: 5, maxWidth: 1200, margin: "0 auto", padding: "48px 48px 80px", display: "grid", gridTemplateColumns: "340px 1fr", gap: 40, alignItems: "start" },
  profileCard: { background: "rgba(20,20,20,0.8)", backdropFilter: "blur(20px)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 24, overflow: "hidden" },
  banner: { height: 100, background: "linear-gradient(135deg, #1DB954 0%, #0a3d1c 50%, #0a0a0a 100%)", position: "relative" },
  bannerOverlay: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0, background: "linear-gradient(0deg, rgba(20,20,20,0.9) 0%, transparent 100%)" },
  avatarRow: { display: "flex", justifyContent: "space-between", alignItems: "flex-end", padding: "0 24px", marginTop: -48, position: "relative", zIndex: 2 },
  avatar: { width: 96, height: 96, borderRadius: "50%", border: "4px solid #1a1a1a", objectFit: "cover", boxShadow: "0 8px 20px rgba(0,0,0,0.3)" },
  avatarPlaceholder: { width: 96, height: 96, borderRadius: "50%", border: "4px solid #1a1a1a", background: "linear-gradient(135deg, #1DB954 0%, #0a3d1c 100%)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 36, fontWeight: 700, color: "#fff", boxShadow: "0 8px 20px rgba(0,0,0,0.3)" },
  statusBadge: { background: "rgba(29,185,84,0.15)", backdropFilter: "blur(4px)", padding: "6px 12px", borderRadius: 20, fontSize: 11, fontWeight: 500, color: "#1DB954", display: "flex", alignItems: "center", gap: 6, marginBottom: 4 },
  statusDot: { width: 6, height: 6, borderRadius: "50%", background: "#1DB954", animation: "pulse 2s infinite" },
  userInfo: { padding: "20px 24px 28px" },
  userName: { fontSize: 26, fontWeight: 700, letterSpacing: "-0.01em", margin: 0, marginBottom: 6, background: "linear-gradient(135deg, #fff 0%, #e0e0e0 100%)", backgroundClip: "text", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" },
  userEmail: { fontSize: 13, color: "#888", margin: 0, marginBottom: 20 },
  divider: { height: 1, background: "rgba(255,255,255,0.06)", margin: "20px 0" },
  statsRow: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 },
  statBox: { background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)", borderRadius: 14, padding: "14px 16px", display: "flex", flexDirection: "column", gap: 6 },
  statValue: { fontSize: 28, fontWeight: 700, color: "#1DB954", lineHeight: 1 },
  statLabel: { fontSize: 11, color: "#888", letterSpacing: "0.02em", fontWeight: 500, display: "flex", alignItems: "center", gap: 6 },
  statIcon: { fontSize: 12 },
  tracksSection: { background: "rgba(20,20,20,0.6)", backdropFilter: "blur(20px)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 24, overflow: "hidden" },
  sectionHeader: { display: "flex", alignItems: "center", gap: 16, padding: "24px 28px 20px", borderBottom: "1px solid rgba(255,255,255,0.06)" },
  sectionTitle: { fontSize: 22, fontWeight: 600, letterSpacing: "-0.01em", margin: 0, color: "#fff" },
  sectionSubtitle: { fontSize: 13, color: "#666", margin: "4px 0 0" },
  waveSmall: { display: "flex", alignItems: "center", gap: 3 },
  barSmall: { display: "block", width: 3, background: "linear-gradient(180deg, #1DB954 0%, #0a3d1c 100%)", borderRadius: 2, opacity: 0.8, animation: "wave 1.4s ease-in-out infinite" },
  trackList: { padding: "4px 0" },
  trackRow: { display: "flex", alignItems: "center", gap: 20, padding: "14px 28px", borderBottom: "1px solid rgba(255,255,255,0.03)", transition: "all 0.2s ease", cursor: "default" },
  trackRowHover: { background: "rgba(255,255,255,0.03)", paddingLeft: 28 },
  trackNumber: { position: "relative" as const, width: 36, textAlign: "center" as const },
  trackIndex: { fontSize: 14, fontWeight: 500, color: "#555" },
  playIcon: { position: "absolute" as const, left: 10, top: -2, fontSize: 10, color: "#1DB954" },
  trackInfo: { flex: 1, display: "flex", flexDirection: "column", gap: 4, overflow: "hidden" },
  trackName: { fontSize: 15, color: "#fff", fontWeight: 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  trackArtist: { fontSize: 12, color: "#777", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  trackMeta: { display: "flex", alignItems: "center", gap: 8 },
  trackTime: { fontSize: 12, color: "#666", whiteSpace: "nowrap", display: "flex", alignItems: "center", gap: 6 },
  previewBtn: { width: 28, height: 28, borderRadius: "50%", background: "#1DB954", border: "none", display: "flex", alignItems: "center", justifyContent: "center", color: "#000", cursor: "pointer", transition: "all 0.2s ease", flexShrink: 0 },
  spotifyLink: { color: "#888", transition: "color 0.2s ease", display: "flex", alignItems: "center", textDecoration: "none" },
  clockIcon: { fontSize: 11 },
  emptyState: { padding: "60px 28px", textAlign: "center" as const },
  emptyIcon: { fontSize: 48, marginBottom: 16, opacity: 0.5 },
  emptyMsg: { color: "#888", fontSize: 14, fontWeight: 500, margin: 0 },
  emptySub: { color: "#555", fontSize: 12, margin: "8px 0 0" },
  loadingWrap: { background: "#0a0a0a", minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 24 },
  waveWrap: { display: "flex", alignItems: "center", gap: 4 },
  bar: { display: "block", width: 4, background: "linear-gradient(180deg, #1DB954 0%, #0a3d1c 100%)", borderRadius: 2, opacity: 0.7, animation: "wave 1.4s ease-in-out infinite" },
  loadingText: { color: "#888", fontSize: 13, letterSpacing: "0.03em", fontFamily: "'Inter', sans-serif", fontWeight: 500 },
};

const waveAnim = `
  @keyframes wave { 0%, 100% { transform: scaleY(1); } 50% { transform: scaleY(0.3); } }
  @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(0.8); } }
`;

const scrollAnim = `
  @media (max-width: 900px) {
    main { grid-template-columns: 1fr !important; padding: 24px !important; gap: 24px !important; }
    .trackRow { padding: 12px 20px !important; }
    .sectionHeader { padding: 20px !important; }
    .profileCard { max-width: 400px; margin: 0 auto; }
  }
`;

const glowAnim = `
  .statBox:hover, .trackRow:hover { transform: translateX(4px); }
  .logoutBtn:hover { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.2); }
`;