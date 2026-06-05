from flask import Blueprint, request
from .service import SpotifyService
from .repository import SpotifyRepository
from app.core.auth_guard import require_auth
from app.core.http import success, not_found, error

spotify_bp = Blueprint("spotify", __name__, url_prefix="/spotify")


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


# ── Playback ────────────────────────────────────────────────────────────────────

@spotify_bp.get("/devices")
@require_auth
def get_devices(token: str, usuario_id: str):
    """Lista dispositivos Spotify disponíveis."""
    return success({"devices": _service(token).get_devices()})


@spotify_bp.get("/playback")
@require_auth
def get_playback(token: str, usuario_id: str):
    """Estado atual do playback."""
    return success(_service(token).get_current_playback_state())


@spotify_bp.post("/play")
@require_auth
def play_track(token: str, usuario_id: str):
    """Toca uma música ou contexto."""
    body = request.get_json(silent=True) or {}
    track_uri    = body.get("track_uri")
    context_uri  = body.get("context_uri")
    device_id    = body.get("device_id")

    svc = _service(token)

    if context_uri:
        return success(svc.play_context(context_uri, device_id))
    elif track_uri:
        return success(svc.play_track(track_uri, device_id))
    else:
        return error("Envie 'track_uri' ou 'context_uri'", 400)


@spotify_bp.post("/pause")
@require_auth
def pause_playback(token: str, usuario_id: str):
    body = request.get_json(silent=True) or {}
    return success(_service(token).pause(body.get("device_id")))


@spotify_bp.post("/next")
@require_auth
def next_track(token: str, usuario_id: str):
    body = request.get_json(silent=True) or {}
    return success(_service(token).next(body.get("device_id")))


@spotify_bp.post("/previous")
@require_auth
def previous_track(token: str, usuario_id: str):
    body = request.get_json(silent=True) or {}
    return success(_service(token).previous(body.get("device_id")))
