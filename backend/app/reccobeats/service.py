import logging
from .repository import ReccoBeatsRepository

logger = logging.getLogger(__name__)


class ReccoBeatsService:
    def __init__(self):
        self.repo = ReccoBeatsRepository()

    def get_audio_features(self, spotify_id: str) -> dict | None:
        """Retorna audio features dado um Spotify Track ID."""
        reccobeats_id = self.repo.get_reccobeats_id(spotify_id)
        if not reccobeats_id:
            logger.error("Track '%s' não encontrada na ReccoBeats.", spotify_id)
            return None

        features = self.repo.get_audio_features(reccobeats_id)
        if features:
            features["spotify_id"]    = spotify_id
            features["reccobeats_id"] = reccobeats_id

        return features

    def get_recommendations(self, spotify_ids: list[str], size: int = 10) -> list[dict]:
        """Retorna recomendações baseadas em uma lista de Spotify Track IDs."""
        return self.repo.get_recommendations(spotify_ids, size)
