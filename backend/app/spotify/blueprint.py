from flask import Blueprint, request
from .service import SpotifyService
from .repository import SpotifyRepository
from app.core.auth_guard import require_auth
from app.core.http import success, not_found, error

spotify_bp = Blueprint("spotify", __name__)


def _service(token: str) -> SpotifyService:
    return SpotifyService(SpotifyRepository(token))


@spotify_bp.get("/profile")
@require_auth
def profile(token: str, usuario_id: str):
    return success(_service(token).get_profile())


@spotify_bp.get("/playlists")
@require_auth
def playlists(token: str, usuario_id: str):
    return success({"playlists": _service(token).get_playlists()})


@spotify_bp.get("/recently-played")
@require_auth
def recently_played(token: str, usuario_id: str):
    return success({"tracks": _service(token).get_recently_played()})


@spotify_bp.get("/top-tracks")
@require_auth
def top_tracks(token: str, usuario_id: str):
    time_range = request.args.get("time_range", "medium_term")
    return success({"tracks": _service(token).get_top_tracks(time_range)})


@spotify_bp.get("/top-artists")
@require_auth
def top_artists(token: str, usuario_id: str):
    time_range = request.args.get("time_range", "medium_term")
    return success({"artists": _service(token).get_top_artists(time_range)})


@spotify_bp.get("/saved-tracks")
@require_auth
def saved_tracks(token: str, usuario_id: str):
    return success({"tracks": _service(token).get_saved_tracks()})


@spotify_bp.get("/search-track")
@require_auth
def search_track(token: str, usuario_id: str):
    query = request.args.get("q")
    if not query:
        return error("Parâmetro 'q' obrigatório", 400, "missing_query")

    svc   = _service(token)
    track = svc.search_track(query)
    if not track:
        return not_found("Nenhuma track encontrada")

    from app.reccobeats.service import ReccoBeatsService
    features = ReccoBeatsService().get_audio_features(track["id"])
    return success({"track": track, "audio_features": features})


@spotify_bp.post("/playlists")
@require_auth
def create_playlist(token: str, usuario_id: str):
    body        = request.get_json(silent=True) or {}
    name        = body.get("name")
    description = body.get("description", "")
    public      = body.get("public", True)

    if not name:
        return error("Campo 'name' obrigatório", 400, "missing_name")

    return success(_service(token).create_playlist(name, description, public), 201)


@spotify_bp.post("/playlists/<playlist_id>/tracks")
@require_auth
def add_tracks(token: str, usuario_id: str, playlist_id: str):
    body       = request.get_json(silent=True) or {}
    track_uris = body.get("uris", [])

    if not track_uris:
        return error("Campo 'uris' obrigatório", 400, "missing_uris")

    _service(token).add_tracks_to_playlist(playlist_id, track_uris)
    return success({"ok": True})