"""
loginTest.py — Login com Spotify (PKCE) usando Flask
Instalar: pip install flask requests spotipy flask-cors flask-session
Rodar:    python loginTest.py
"""

import os, hashlib, base64, secrets
import urllib.parse
import requests
from flask import Flask, redirect, request, session, jsonify
from flask_cors import CORS
from flask_session import Session
from functions import (
    get_playlists, get_recently_played,
    get_top_tracks, get_top_artists,
    get_saved_tracks, search_track,
    get_track_audio_features
)

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY", "troca-por-uma-chave-fixa-qualquer-aqui")

# ── Sessões server-side (filesystem) ──────────────────────────────────────────
# Isso evita problemas com cookies cross-port (localhost:5000 vs :8080).
# O session ID é um cookie simples; os dados ficam em /tmp/flask_session/
app.config["SESSION_TYPE"]            = "filesystem"
app.config["SESSION_FILE_DIR"]        = "/tmp/flask_session"
app.config["SESSION_PERMANENT"]       = False
app.config["SESSION_USE_SIGNER"]      = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"]   = False   # localhost não usa HTTPS
app.config["SESSION_COOKIE_DOMAIN"]   = None
Session(app)

# ── Configuração ───────────────────────────────────────────────────────────────
CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID", "b5727e21ded847928278e6fe1782060f")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5000/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:8080")
SCOPES = " ".join([
    "user-read-private",
    "user-read-email",
    "user-library-read",
    "user-top-read",
    "user-read-recently-played",
    "playlist-read-private",
    "playlist-modify-public",
    "playlist-modify-private",
])

AUTH_URL  = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE  = "https://api.spotify.com/v1"

CORS(app, origins=[FRONTEND_URL], supports_credentials=True)


# ── Helpers ────────────────────────────────────────────────────────────────────
def unauthorized():
    return jsonify({"error": "not_authenticated"}), 401




def get_current_user():
    token = session.get("access_token")
    if not token:
        return None, None

    me = requests.get(f"{API_BASE}/me", headers={"Authorization": f"Bearer {token}"})
    if me.status_code == 401:
        session.clear()
        return None, 401
    if not me.ok:
        return None, me.status_code

    user = me.json()
    return {
        "name":         user.get("display_name", "Usuário"),
        "display_name": user.get("display_name", "Usuário"),
        "email":        user.get("email", ""),
        "followers":    user.get("followers", {}).get("total", 0),
        "avatar":       (user.get("images") or [{}])[0].get("url", ""),
        "plan":         user.get("product", "free").upper(),
        "product":      user.get("product", "free"),
        "images":       user.get("images", []),
    }, None


# ── PKCE ───────────────────────────────────────────────────────────────────────
def make_verifier():
    return base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode()

def make_challenge(verifier):
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


# ── Rotas de autenticação ──────────────────────────────────────────────────────
@app.route("/debug-cookie")#teste
def debug_cookie():
    return jsonify({"session_cookie": request.cookies.get("session")})

@app.route("/token-scopes")#teste
def token_scopes():
    token = session.get("access_token")
    if not token:
        return unauthorized()
    return jsonify({"scopes_configured": SCOPES.split()})



@app.route("/")
def index():
    if "access_token" in session:
        return redirect(f"{FRONTEND_URL}/profile")
    return redirect(f"{FRONTEND_URL}/login")


@app.route("/login")
def login():
    verifier  = make_verifier()
    challenge = make_challenge(verifier)
    state     = secrets.token_urlsafe(16)

    session["verifier"] = verifier
    session["state"]    = state

    params = urllib.parse.urlencode({
        "client_id":             CLIENT_ID,
        "response_type":         "code",
        "redirect_uri":          REDIRECT_URI,
        "scope":                 SCOPES,
        "state":                 state,
        "code_challenge_method": "S256",
        "code_challenge":        challenge,
    })
    return redirect(f"{AUTH_URL}?{params}")


@app.route("/callback")
def callback():
    error = request.args.get("error")
    if error:
        return redirect(f"{FRONTEND_URL}/entrar?error={urllib.parse.quote(error)}")

    if request.args.get("state") != session.get("state"):
        return redirect(f"{FRONTEND_URL}/entrar?error=state_invalido")

    code = request.args.get("code")
    resp = requests.post(TOKEN_URL, data={
        "grant_type":    "authorization_code",
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
        "client_id":     CLIENT_ID,
        "code_verifier": session.pop("verifier", ""),
    })

    if not resp.ok:
        return redirect(f"{FRONTEND_URL}/entrar?error=token_failed")

    tokens = resp.json()
    session["access_token"]  = tokens["access_token"]
    session["refresh_token"] = tokens.get("refresh_token")
    return redirect(f"{FRONTEND_URL}/profile")


@app.route("/profile")
def profile():
    user, error_status = get_current_user()
    if user is None:
        if error_status is None or error_status == 401:
            return unauthorized()
        return jsonify({"error": "spotify_request_failed"}), error_status
    return jsonify(user)


@app.route("/logout")
def logout():
    session.clear()
    return "", 204


@app.route("/debug-session")
def debug_session():
    """Endpoint temporário para diagnóstico — remover em produção."""
    return jsonify({
        "cookies_received":  dict(request.cookies),
        "session_keys":      list(session.keys()),
        "has_access_token":  "access_token" in session,
    })


# ── Rotas de dados do Spotify ──────────────────────────────────────────────────

@app.route("/playlists")
def playlists():
    token = session.get("access_token")
    if not token:
        return unauthorized()
    return jsonify({"playlists": get_playlists(token)})


@app.route("/recently-played")
def recently_played():
    token = session.get("access_token")
    if not token:
        return unauthorized()
    return jsonify({"tracks": get_recently_played(token)})


@app.route("/top-tracks")
def top_tracks():
    token = session.get("access_token")
    if not token:
        return unauthorized()
    return jsonify({"tracks": get_top_tracks(token)})


@app.route("/top-artists")
def top_artists():
    token = session.get("access_token")
    if not token:
        return unauthorized()
    return jsonify({"artists": get_top_artists(token)})


@app.route("/saved-tracks")
def saved_tracks():
    token = session.get("access_token")
    if not token:
        return unauthorized()
    return jsonify({"tracks": get_saved_tracks(token)})


@app.route("/search-track")
def search_track_route():
    token = session.get("access_token")
    if not token:
        return unauthorized()
 
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Missing query parameter 'q'"}), 400
 
    tracks = search_track(token, query, limit=1)
    if not tracks:
        return jsonify({"error": "No track found"}), 404
 
    track = tracks[0]
    track_id = track['id']

    features = get_track_audio_features(track_id) 
 
    response = {
        "track": {
            "name":          track['name'],
            "artists":       [artist['name'] for artist in track['artists']],
            "album":         track['album']['name'],
            "id":            track_id,
            "uri":           track['uri'],
            "duration_ms":   track['duration_ms'],
            "explicit":      track['explicit'],
            "popularity":    track.get('popularity', 0),
            "preview_url":   track.get('preview_url'),
            "external_urls": track['external_urls'],
        },
        "audio_features": features,   # None se a track não estiver na ReccoBeats
    }
    return jsonify(response)
 


# ── Inicia o servidor ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "true").lower() == "true",
    )