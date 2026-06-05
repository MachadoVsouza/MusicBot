import spotipy


class SpotifyRepository:
    """Acesso direto à API do Spotify via Spotipy."""

    def __init__(self, access_token: str):
        self._sp = spotipy.Spotify(auth=access_token)

    def get_current_user(self) -> dict:
        return self._sp.current_user()

    def get_playlists(self, limit: int = 10) -> dict:
        return self._sp.current_user_playlists(limit=limit)

    def get_recently_played(self, limit: int = 10) -> dict:
        return self._sp.current_user_recently_played(limit=limit)

    def get_top_tracks(self, time_range: str = "medium_term", limit: int = 10) -> dict:
        return self._sp.current_user_top_tracks(limit=limit, time_range=time_range)

    def get_top_artists(self, time_range: str = "medium_term", limit: int = 10) -> dict:
        return self._sp.current_user_top_artists(limit=limit, time_range=time_range)

    def get_saved_tracks(self, limit: int = 10) -> dict:
        return self._sp.current_user_saved_tracks(limit=limit)

    def search_track(self, query: str, limit: int = 1) -> list:
        results = self._sp.search(q=query, type="track", limit=limit)
        return results["tracks"]["items"]

    def create_playlist(self, user_id: str, name: str, description: str = "", public: bool = True) -> dict:
        return self._sp.user_playlist_create(
            user=user_id,
            name=name,
            public=public,
            description=description,
        )

    def add_tracks_to_playlist(self, playlist_id: str, track_uris: list[str]) -> None:
        self._sp.playlist_add_items(playlist_id, track_uris)

    # ── Playback ──────────────────────────────────────────────────────────────

    def get_available_devices(self) -> list[dict]:
        """Retorna dispositivos disponíveis para playback."""
        devices = self._sp.devices()
        return devices.get("devices", [])

    def start_playback(
        self,
        device_id: str | None = None,
        uris: list[str] | None = None,
        context_uri: str | None = None,
        offset: dict | None = None,
        position_ms: int = 0,
    ) -> bool:
        """
        Inicia playback em um dispositivo.
        - device_id: None = usa o dispositivo ativo
        - uris: lista de tracks URIs para tocar
        - context_uri: URI de playlist/album/artist
        """
        try:
            self._sp.start_playback(
                device_id=device_id,
                uris=uris,
                context_uri=context_uri,
                offset=offset,
                position_ms=position_ms,
            )
            return True
        except spotipy.SpotifyException as e:
            if e.http_status == 404:
                # Nenhum dispositivo ativo
                return False
            raise

    def pause_playback(self, device_id: str | None = None) -> bool:
        """Pausa o playback."""
        try:
            self._sp.pause_playback(device_id=device_id)
            return True
        except spotipy.SpotifyException:
            return False

    def next_track(self, device_id: str | None = None) -> bool:
        """Próxima faixa."""
        try:
            self._sp.next_track(device_id=device_id)
            return True
        except spotipy.SpotifyException:
            return False

    def previous_track(self, device_id: str | None = None) -> bool:
        """Faixa anterior."""
        try:
            self._sp.previous_track(device_id=device_id)
            return True
        except spotipy.SpotifyException:
            return False

    def get_current_playback(self) -> dict | None:
        """Retorna o estado atual do playback."""
        try:
            return self._sp.current_playback()
        except spotipy.SpotifyException:
            return None

    def seek_track(self, position_ms: int, device_id: str | None = None) -> bool:
        """Pula para uma posição na faixa atual."""
        try:
            self._sp.seek_track(position_ms, device_id=device_id)
            return True
        except spotipy.SpotifyException:
            return False

    def shuffle(self, state: bool, device_id: str | None = None) -> bool:
        """Ativa/desativa shuffle."""
        try:
            self._sp.shuffle(state, device_id=device_id)
            return True
        except spotipy.SpotifyException:
            return False

    def repeat(self, state: str, device_id: str | None = None) -> bool:
        """Define modo de repetição: 'track', 'context' ou 'off'."""
        try:
            self._sp.repeat(state, device_id=device_id)
            return True
        except spotipy.SpotifyException:
            return False
