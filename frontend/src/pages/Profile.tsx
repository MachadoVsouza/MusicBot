import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

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
}

function timeAgo(dateStr: string): string {
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (diff < 60) return "agora";
  if (diff < 3600) return `${Math.floor(diff / 60)}min atrás`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h atrás`;
  return `${Math.floor(diff / 86400)}d atrás`;
}

export default function Profile() {
  const navigate = useNavigate();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [profileRes, tracksRes] = await Promise.all([
          fetch(`${API}/profile`, { credentials: "include" }),
          fetch(`${API}/recently-played`, { credentials: "include" }),
        ]);




        if (!profileRes.ok) {
          // MOCK para teste — remova depois
          setUser({
            name: "Usuário Teste",
            email: "teste@email.com",
            avatar: "",
            plan: "FREE",
            followers: 42,
          });
          setTracks([
            { name: "Bohemian Rhapsody", artist: "Queen", album: "A Night at the Opera", played_at: new Date(Date.now() - 300000).toISOString() },
            { name: "Blinding Lights", artist: "The Weeknd", album: "After Hours", played_at: new Date(Date.now() - 3600000).toISOString() },
            { name: "Levitating", artist: "Dua Lipa", album: "Future Nostalgia", played_at: new Date(Date.now() - 7200000).toISOString() },
          ]);
          return;
        }


        /*
                if (!profileRes.ok) {
                  navigate("/login");
                  return;
                }
        */
        const profileData = await profileRes.json();
        setUser({
          name: profileData.display_name ?? profileData.name ?? "",
          email: profileData.email ?? "",
          avatar: profileData.avatar ?? profileData.images?.[0]?.url ?? "",
          plan: profileData.plan ?? "FREE",
          followers: profileData.followers ?? 0,
        });

        if (tracksRes.ok) {
          const tracksData = await tracksRes.json();
          setTracks(tracksData.tracks ?? []);
        }
      } catch {
        navigate("/login");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [navigate]);

  async function handleLogout() {
    await fetch(`${API}/logout`, { credentials: "include" });
    navigate("/login");
  }

  if (loading) {
    return (
      <div style={styles.loadingWrap}>
        <div style={styles.waveWrap}>
          {[12, 28, 18, 38, 22, 32, 14, 24, 36, 16].map((h, i) => (
            <span
              key={i}
              style={{
                ...styles.bar,
                height: h,
                animationDelay: `${i * 0.07}s`,
              }}
            />
          ))}
        </div>
        <p style={styles.loadingText}>Carregando perfil...</p>
        <style>{waveAnim}</style>
      </div>
    );
  }

  if (!user) return null;

  const initials = user.name.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase();

  return (
    <div style={styles.page}>
      <style>{waveAnim + scrollAnim}</style>

      {/* Header */}
      <header style={styles.header}>
        <span style={styles.brand}>MUSICBOT</span>
        <button style={styles.logoutBtn} onClick={handleLogout}>
          Sair
        </button>
      </header>

      <main style={styles.main}>
        {/* Profile card */}
        <div style={styles.profileCard}>
          <div style={styles.banner} />
          <div style={styles.avatarRow}>
            {user.avatar ? (
              <img src={user.avatar} alt={user.name} style={styles.avatar} />
            ) : (
              <div style={styles.avatarPlaceholder}>{initials}</div>
            )}
            <span style={styles.connectedBadge}>● Conectado</span>
          </div>
          <div style={styles.userInfo}>
            <h1 style={styles.userName}>{user.name}</h1>
            <p style={styles.userEmail}>{user.email}</p>
            <div style={styles.statsRow}>
              <div style={styles.statBox}>
                <span style={styles.statValue}>{user.followers.toLocaleString("pt-BR")}</span>
                <span style={styles.statLabel}>SEGUIDORES</span>
              </div>
              <div style={styles.statBox}>
                <span style={styles.statValue}>{user.plan}</span>
                <span style={styles.statLabel}>PLANO</span>
              </div>
            </div>
          </div>
        </div>

        {/* Recently played */}
        <div style={styles.tracksSection}>
          <div style={styles.sectionHeader}>
            <div style={styles.waveSmall}>
              {[8, 16, 10, 20, 12].map((h, i) => (
                <span key={i} style={{ ...styles.barSmall, height: h, animationDelay: `${i * 0.1}s` }} />
              ))}
            </div>
            <h2 style={styles.sectionTitle}>Ouvidas recentemente</h2>
          </div>

          <div style={styles.trackList}>
            {tracks.length === 0 ? (
              <p style={styles.emptyMsg}>Nenhuma música encontrada.</p>
            ) : (
              tracks.map((track, i) => (
                <div key={i} style={styles.trackRow}>
                  <span style={styles.trackIndex}>{String(i + 1).padStart(2, "0")}</span>
                  <div style={styles.trackInfo}>
                    <span style={styles.trackName}>{track.name}</span>
                    <span style={styles.trackArtist}>{track.artist} · {track.album}</span>
                  </div>
                  <span style={styles.trackTime}>{timeAgo(track.played_at)}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  page: {
    background: "#080808",
    minHeight: "100vh",
    fontFamily: "'DM Sans', sans-serif",
    color: "#f0ede8",
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "20px 40px",
    borderBottom: "1px solid #1e1e1e",
  },
  brand: {
    fontFamily: "'Bebas Neue', sans-serif",
    fontSize: 20,
    letterSpacing: "0.15em",
    color: "#1DB954",
  },
  logoutBtn: {
    background: "transparent",
    border: "1px solid #2a2a2a",
    color: "#666",
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 13,
    padding: "8px 20px",
    borderRadius: 6,
    cursor: "pointer",
  },
  main: {
    maxWidth: 860,
    margin: "0 auto",
    padding: "40px 24px",
    display: "grid",
    gridTemplateColumns: "300px 1fr",
    gap: 32,
    alignItems: "start",
  },
  profileCard: {
    background: "#111",
    border: "1px solid #1e1e1e",
    borderRadius: 16,
    overflow: "hidden",
  },
  banner: {
    height: 80,
    background: "linear-gradient(135deg,#0f3d20 0%,#1a1a1a 60%,#0d2b17 100%)",
  },
  avatarRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-end",
    padding: "0 20px",
    marginTop: -36,
    position: "relative",
    zIndex: 1,
  },
  avatar: {
    width: 72,
    height: 72,
    borderRadius: "50%",
    border: "3px solid #080808",
    objectFit: "cover",
  },
  avatarPlaceholder: {
    width: 72,
    height: 72,
    borderRadius: "50%",
    border: "3px solid #080808",
    background: "#1a1a1a",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontFamily: "'Bebas Neue', sans-serif",
    fontSize: 28,
    color: "#1DB954",
  },
  connectedBadge: {
    fontSize: 11,
    color: "#1DB954",
    letterSpacing: "0.05em",
    marginBottom: 4,
  },
  userInfo: {
    padding: "12px 20px 24px",
  },
  userName: {
    fontFamily: "'Bebas Neue', sans-serif",
    fontSize: 28,
    letterSpacing: "0.04em",
    margin: 0,
    marginBottom: 4,
  },
  userEmail: {
    fontSize: 12,
    color: "#555",
    margin: 0,
    marginBottom: 20,
  },
  statsRow: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 10,
  },
  statBox: {
    background: "#080808",
    border: "1px solid #1e1e1e",
    borderRadius: 10,
    padding: "12px 14px",
    display: "flex",
    flexDirection: "column" as const,
    gap: 4,
  },
  statValue: {
    fontFamily: "'Bebas Neue', sans-serif",
    fontSize: 24,
    color: "#1DB954",
    lineHeight: 1,
  },
  statLabel: {
    fontSize: 10,
    color: "#444",
    letterSpacing: "0.08em",
  },
  tracksSection: {
    background: "#111",
    border: "1px solid #1e1e1e",
    borderRadius: 16,
    overflow: "hidden",
  },
  sectionHeader: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    padding: "20px 24px 16px",
    borderBottom: "1px solid #1a1a1a",
  },
  sectionTitle: {
    fontFamily: "'Bebas Neue', sans-serif",
    fontSize: 20,
    letterSpacing: "0.06em",
    margin: 0,
    color: "#f0ede8",
  },
  waveSmall: {
    display: "flex",
    alignItems: "center",
    gap: 2,
  },
  barSmall: {
    display: "block",
    width: 2,
    background: "#1DB954",
    borderRadius: 2,
    opacity: 0.7,
    animation: "wave 1.4s ease-in-out infinite",
  },
  trackList: {
    padding: "8px 0",
  },
  trackRow: {
    display: "flex",
    alignItems: "center",
    gap: 16,
    padding: "12px 24px",
    borderBottom: "1px solid #141414",
    transition: "background 0.15s",
  },
  trackIndex: {
    fontFamily: "'Bebas Neue', sans-serif",
    fontSize: 16,
    color: "#333",
    minWidth: 24,
    textAlign: "center" as const,
  },
  trackInfo: {
    flex: 1,
    display: "flex",
    flexDirection: "column" as const,
    gap: 2,
    overflow: "hidden",
  },
  trackName: {
    fontSize: 14,
    color: "#f0ede8",
    fontWeight: 500,
    whiteSpace: "nowrap" as const,
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  trackArtist: {
    fontSize: 12,
    color: "#555",
    whiteSpace: "nowrap" as const,
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  trackTime: {
    fontSize: 11,
    color: "#444",
    whiteSpace: "nowrap" as const,
  },
  emptyMsg: {
    padding: "32px 24px",
    color: "#444",
    fontSize: 13,
    textAlign: "center" as const,
  },
  loadingWrap: {
    background: "#080808",
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    justifyContent: "center",
    gap: 20,
  },
  waveWrap: {
    display: "flex",
    alignItems: "center",
    gap: 3,
  },
  bar: {
    display: "block",
    width: 3,
    background: "#1DB954",
    borderRadius: 2,
    opacity: 0.7,
    animation: "wave 1.4s ease-in-out infinite",
  },
  loadingText: {
    color: "#444",
    fontSize: 13,
    letterSpacing: "0.06em",
    fontFamily: "'DM Sans', sans-serif",
  },
};

const waveAnim = `
  @keyframes wave {
    0%, 100% { transform: scaleY(1); }
    50% { transform: scaleY(0.3); }
  }
`;

const scrollAnim = `
  @media (max-width: 700px) {
    main { grid-template-columns: 1fr !important; }
  }
`;
