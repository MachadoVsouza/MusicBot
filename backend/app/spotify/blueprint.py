from flask import Blueprint, request, current_app
from .service import SpotifyService
from .repository import SpotifyRepository
from app.auth.repository import AuthRepository
from app.core.http import success, unauthorized, not_found, error

spotify_bp = Blueprint("spotify", __name__)


def _get_token() -> str | None:
    return AuthRepository().get_access_token()


def _service(token: str) -> SpotifyService:
    return SpotifyService(SpotifyRepository(token))


# ── Perfil (mantém rota /profile para compatibilidade com o frontend) ─────────

@spotify_bp.get("/profile")
def profile():
    token = _get_token()
    if not token:
        return unauthorized()
    return success(_service(token).get_profile())


# ── Rotas de dados ────────────────────────────────────────────────────────────

@spotify_bp.get("/playlists")
def playlists():
    token = _get_token()
    if not token:
        return unauthorized()
    return success({"playlists": _service(token).get_playlists()})


@spotify_bp.get("/recently-played")
def recently_played():
    token = _get_token()
    if not token:
        return unauthorized()
    return success({"tracks": _service(token).get_recently_played()})


@spotify_bp.get("/top-tracks")
def top_tracks():
    token = _get_token()
    if not token:
        return unauthorized()
    time_range = request.args.get("time_range", "medium_term")
    return success({"tracks": _service(token).get_top_tracks(time_range)})


@spotify_bp.get("/top-artists")
def top_artists():
    token = _get_token()
    if not token:
        return unauthorized()
    time_range = request.args.get("time_range", "medium_term")
    return success({"artists": _service(token).get_top_artists(time_range)})


@spotify_bp.get("/saved-tracks")
def saved_tracks():
    token = _get_token()
    if not token:
        return unauthorized()
    return success({"tracks": _service(token).get_saved_tracks()})


@spotify_bp.get("/search-track")
def search_track():
    token = _get_token()
    if not token:
        return unauthorized()

    query = request.args.get("q")
    if not query:
        return error("Parâmetro 'q' obrigatório", 400, "missing_query")

    svc   = _service(token)
    track = svc.search_track(query)
    if not track:
        return not_found("Nenhuma track encontrada")

    # Busca audio features via ReccoBeats
    from app.reccobeats.service import ReccoBeatsService
    features = ReccoBeatsService().get_audio_features(track["id"])

    return success({"track": track, "audio_features": features})


# ── Playlists (write) ─────────────────────────────────────────────────────────

@spotify_bp.post("/playlists")
def create_playlist():
    token = _get_token()
    if not token:
        return unauthorized()

    body        = request.get_json(silent=True) or {}
    name        = body.get("name")
    description = body.get("description", "")
    public      = body.get("public", True)

    if not name:
        return error("Campo 'name' obrigatório", 400, "missing_name")

    return success(_service(token).create_playlist(name, description, public), 201)


@spotify_bp.post("/playlists/<playlist_id>/tracks")
def add_tracks(playlist_id: str):
    token = _get_token()
    if not token:
        return unauthorized()

    body       = request.get_json(silent=True) or {}
    track_uris = body.get("uris", [])

    if not track_uris:
        return error("Campo 'uris' obrigatório", 400, "missing_uris")

    _service(token).add_tracks_to_playlist(playlist_id, track_uris)
    return success({"ok": True})
