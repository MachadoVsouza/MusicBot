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
