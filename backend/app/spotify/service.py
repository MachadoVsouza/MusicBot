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
                "total": item.get("tracks", {}).get("total", 0) if item.get("tracks") else 0,
                "url":   item["external_urls"]["spotify"],
            }
            for item in results["items"]
            if item
        ]
        
    # ── Histórico ─────────────────────────────────────────────────────────────

    def get_recently_played(self) -> list[dict]:
        results = self.repo.get_recently_played()
        return [
            {
                "name":        item["track"]["name"],
                "artist":      item["track"]["artists"][0]["name"],
                "album":       item["track"]["album"]["name"],
                "played_at":   item["played_at"],
                "preview_url": item["track"].get("preview_url"),
                "spotify_url": item["track"]["external_urls"].get("spotify"),
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

    # ── Artista ───────────────────────────────────────────────────────────────

    def get_artist_info(self, nome: str) -> dict | None:
        """Busca informações de um artista via Spotipy."""
        artista = self.repo.search_artist(nome)
        if not artista:
            return None
        top_tracks = self.repo.get_artist_top_tracks(artista["id"])
        return {
            "nome":         artista["name"],
            "generos":      artista.get("genres", []),
            "popularidade": artista.get("popularity"),
            "seguidores":   artista["followers"]["total"],
            "top_musicas":  [t["name"] for t in top_tracks[:5]],
            "url":          artista["external_urls"].get("spotify"),
            "uri":          artista["uri"],
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

    def create_playlist_with_tracks(self, name: str, description: str, track_uris: list[str]) -> dict:
        """Cria uma playlist e adiciona tracks."""
        result = self.create_playlist(name, description)
        if result.get("id"):
            self.add_tracks_to_playlist(result["id"], track_uris)
        return result

    # ── Playback ──────────────────────────────────────────────────────────────

    def get_devices(self) -> list[dict]:
        return self.repo.get_available_devices()

    def play_track(self, track_uri: str, device_id: str | None = None) -> dict:
        success = self.repo.start_playback(device_id=device_id, uris=[track_uri])
        if not success:
            return {"erro": "Nenhum dispositivo ativo encontrado. Abra o Spotify em algum dispositivo primeiro."}
        return {"ok": True, "mensagem": "Música tocando no seu Spotify!"}

    def play_context(self, context_uri: str, device_id: str | None = None) -> dict:
        success = self.repo.start_playback(device_id=device_id, context_uri=context_uri)
        if not success:
            return {"erro": "Nenhum dispositivo ativo encontrado."}
        return {"ok": True, "mensagem": "Tocando no seu Spotify!"}

    def pause(self, device_id: str | None = None) -> dict:
        success = self.repo.pause_playback(device_id)
        return {"ok": success, "mensagem": "Playback pausado." if success else "Não foi possível pausar."}

    def next(self, device_id: str | None = None) -> dict:
        success = self.repo.next_track(device_id)
        return {"ok": success, "mensagem": "Próxima faixa." if success else "Não foi possível avançar."}

    def previous(self, device_id: str | None = None) -> dict:
        success = self.repo.previous_track(device_id)
        return {"ok": success, "mensagem": "Faixa anterior." if success else "Não foi possível voltar."}

    def transfer_to_device(self, device_id: str) -> dict:
        """Transfere o playback para um dispositivo específico."""
        success = self.repo.transfer_playback(device_id)
        if not success:
            return {"erro": "Não foi possível transferir o playback para este dispositivo."}
        devices = self.get_devices()
        nome = next((d["name"] for d in devices if d["id"] == device_id), "dispositivo selecionado")
        return {"ok": True, "mensagem": f"Playback transferido para {nome}!"}

    def add_to_queue(self, track_uri: str, device_id: str | None = None) -> dict:
        """Adiciona uma música na fila de playback."""
        success = self.repo.add_to_queue(track_uri, device_id)
        if not success:
            return {"erro": "Nenhum dispositivo ativo. Abra o Spotify em algum dispositivo."}
        return {"ok": True, "mensagem": "Música adicionada à fila!"}

    def get_current_playback_state(self) -> dict | None:
        playback = self.repo.get_current_playback()
        if not playback:
            return {"playing": False, "device": None, "track": None}
        track = playback.get("item")
        return {
            "playing":     playback.get("is_playing", False),
            "progress_ms": playback.get("progress_ms", 0),
            "device":      playback.get("device"),
            "track":       {
                "name":    track.get("name") if track else None,
                "artists": [a["name"] for a in track.get("artists", [])] if track else [],
                "album":   track.get("album", {}).get("name") if track else None,
                "uri":     track.get("uri") if track else None,
                "url":     track.get("external_urls", {}).get("spotify") if track else None,
            } if track else None,
        }