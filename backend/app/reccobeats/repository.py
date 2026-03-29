import logging
from .client import ReccoBeatsClient

logger = logging.getLogger(__name__)


class ReccoBeatsRepository:
    def __init__(self):
        self._client = ReccoBeatsClient()

    def get_reccobeats_id(self, spotify_id: str) -> str | None:
        """Mapeia um Spotify Track ID para o ID interno da ReccoBeats."""
        data = self._client.get("/track", params={"ids": spotify_id})

        if isinstance(data, list) and data:
            return data[0].get("id")

        if isinstance(data, dict):
            items = data.get("content") or data.get("items") or data.get("tracks") or []
            if items:
                return items[0].get("id")

        logger.warning("Não foi possível mapear spotify_id '%s'.", spotify_id)
        return None

    def get_audio_features(self, reccobeats_id: str) -> dict | None:
        return self._client.get(f"/track/{reccobeats_id}/audio-features")

    def get_recommendations(self, seed_ids: list[str], size: int = 10) -> list[dict]:
        params = [("seeds", sid) for sid in seed_ids] + [("size", size)]
        data   = self._client.get("/track/recommendation", params=params)

        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("content") or data.get("tracks") or []
        return []
