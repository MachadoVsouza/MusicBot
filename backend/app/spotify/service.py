from .repository import SpotifyRepository


class SpotifyService:
    def __init__(self, repo: SpotifyRepository):
        self.repo = repo

    # ── Perfil ────────────────────────────────────────────────────────────────

    def get_profile(self) -> dict:
        user = self.repo.get_current_user()
        return {
            "id":           user.get("id"),
            "name":         user.get("display_name", "Usuário"),
            "display_name": user.get("display_name", "Usuário"),
            "email":        user.get("email", ""),
            "followers":    user.get("followers", {}).get("total", 0),
            "avatar":       (user.get("images") or [{}])[0].get("url", ""),
            "plan":         user.get("product", "free").upper(),
            "product":      user.get("product", "free"),
            "images":       user.get("images", []),
        }

    # ── Playlists ─────────────────────────────────────────────────────────────

    def get_playlists(self) -> list[dict]:
        results = self.repo.get_playlists()
        return [
            {
                "id":    item["id"],
                "name":  item["name"],
                "total": item["tracks"]["total"],
            }
            for item in results["items"]
        ]

    # ── Histórico ─────────────────────────────────────────────────────────────

    def get_recently_played(self) -> list[dict]:
        results = self.repo.get_recently_played()
        return [
            {
                "name":      item["track"]["name"],
                "artist":    item["track"]["artists"][0]["name"],
                "album":     item["track"]["album"]["name"],
                "played_at": item["played_at"],
            }
            for item in results["items"]
        ]

    # ── Top tracks / artists ──────────────────────────────────────────────────

    def get_top_tracks(self, time_range: str = "medium_term") -> list[dict]:
        results = self.repo.get_top_tracks(time_range=time_range)
        return [
            {"name": t["name"], "artist": t["artists"][0]["name"]}
            for t in results["items"]
        ]

    def get_top_artists(self, time_range: str = "medium_term") -> list[dict]:
        results = self.repo.get_top_artists(time_range=time_range)
        return [{"name": a["name"]} for a in results["items"]]

    # ── Saved tracks ──────────────────────────────────────────────────────────

    def get_saved_tracks(self) -> list[dict]:
        results = self.repo.get_saved_tracks()
        return [
            {
                "name":     item["track"]["name"],
                "artist":   item["track"]["artists"][0]["name"],
                "added_at": item["added_at"],
            }
            for item in results["items"]
        ]

    # ── Busca de track ────────────────────────────────────────────────────────

    def search_track(self, query: str) -> dict | None:
        """Retorna dados formatados da primeira track encontrada."""
        tracks = self.repo.search_track(query, limit=1)
        if not tracks:
            return None

        track = tracks[0]
        return {
            "id":            track["id"],
            "name":          track["name"],
            "artists":       [a["name"] for a in track["artists"]],
            "album":         track["album"]["name"],
            "uri":           track["uri"],
            "duration_ms":   track["duration_ms"],
            "explicit":      track["explicit"],
            "popularity":    track.get("popularity", 0),
            "preview_url":   track.get("preview_url"),
            "external_urls": track["external_urls"],
        }

    # ── Playlists (write) ─────────────────────────────────────────────────────

    def create_playlist(self, name: str, description: str = "", public: bool = True) -> dict:
        profile  = self.get_profile()
        playlist = self.repo.create_playlist(profile["id"], name, description, public)
        return {
            "id":  playlist["id"],
            "url": playlist["external_urls"]["spotify"],
        }

    def add_tracks_to_playlist(self, playlist_id: str, track_uris: list[str]) -> bool:
        self.repo.add_tracks_to_playlist(playlist_id, track_uris)
        return True
