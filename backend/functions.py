import spotipy
from spotipy.oauth2 import SpotifyOAuth
from recco_beats import get_audio_features as recco_get_audio_features
from recco_beats import get_audio_features as recco_get_audio_features


# ── Inicializa o cliente Spotipy com o token já obtido via PKCE ────────────────
def get_client(token):
    """Retorna um cliente Spotipy autenticado com o access token da sessão."""
    return spotipy.Spotify(auth=token)


# ── Playlists ──────────────────────────────────────────────────────────────────
def get_playlists(token):
    """Retorna as 10 primeiras playlists do usuário."""
    sp = get_client(token)
    results = sp.current_user_playlists(limit=10)
    return [
        {
            "name":  item["name"],
            "total": item["tracks"]["total"],
            "id":    item["id"],
        }
        for item in results["items"]
    ]


# ── Histórico recente ──────────────────────────────────────────────────────────
def get_recently_played(token):
    """Retorna as 10 últimas músicas ouvidas."""
    sp = get_client(token)
    results = sp.current_user_recently_played(limit=10)
    return [
        {
            "name":      item["track"]["name"],
            "artist":    item["track"]["artists"][0]["name"],
            "album":     item["track"]["album"]["name"],
            "played_at": item["played_at"],
        }
        for item in results["items"]
    ]


# ── Top músicas ────────────────────────────────────────────────────────────────
def get_top_tracks(token, time_range="medium_term"):
    """
    Retorna as 10 músicas mais ouvidas.
    time_range: short_term (4 sem) | medium_term (6 meses) | long_term (anos)
    """
    sp = get_client(token)
    results = sp.current_user_top_tracks(limit=10, time_range=time_range)
    return [
        {
            "name":   track["name"],
            "artist": track["artists"][0]["name"],
        }
        for track in results["items"]
    ]


# ── Top artistas ───────────────────────────────────────────────────────────────
def get_top_artists(token, time_range="medium_term"):
    """Retorna os 10 artistas mais ouvidos."""
    sp = get_client(token)
    results = sp.current_user_top_artists(limit=10, time_range=time_range)
    return [
        {
            "name": artist["name"],
        }
        for artist in results["items"]
    ]


# ── Músicas curtidas ───────────────────────────────────────────────────────────
def get_saved_tracks(token):
    """Retorna as 10 músicas curtidas (Liked Songs)."""
    sp = get_client(token)
    results = sp.current_user_saved_tracks(limit=10)
    return [
        {
            "name":     item["track"]["name"],
            "artist":   item["track"]["artists"][0]["name"],
            "added_at": item["added_at"],
        }
        for item in results["items"]
    ]


# ── Criar playlist ─────────────────────────────────────────────────────────────
def create_playlist(token, name, description="", public=True):
    """Cria uma nova playlist para o usuário."""
    sp = get_client(token)
    user_id = sp.current_user()["id"]
    playlist = sp.user_playlist_create(
        user=user_id,
        name=name,
        public=public,
        description=description
    )
    return {
        "id":  playlist["id"],
        "url": playlist["external_urls"]["spotify"],
    }


# ── Adicionar músicas à playlist ───────────────────────────────────────────────
def add_tracks_to_playlist(token, playlist_id, track_uris):
    """Adiciona uma lista de track URIs a uma playlist."""
    sp = get_client(token)
    sp.playlist_add_items(playlist_id, track_uris)
    return True


# ── Buscar track ───────────────────────────────────────────────────────────────
def search_track(token, query, limit=1):
    sp = get_client(token)
    results = sp.search(q=query, type='track', limit=limit)
    return results['tracks']['items']


# ── Audio features via ReccoBeats ──────────────────────────────────────────────
def get_track_audio_features(spotify_track_id: str) -> dict | None:
    """
    Retorna audio features via ReccoBeats (substitui o Spotify depreciado).
    Recebe apenas o Spotify Track ID — sem token necessário.
    """
    return recco_get_audio_features(spotify_track_id)