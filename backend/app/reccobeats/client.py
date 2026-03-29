import logging
import requests
from flask import current_app

logger = logging.getLogger(__name__)


class ReccoBeatsClient:
    """Cliente HTTP para a API da ReccoBeats."""

    def _base(self) -> str:
        return current_app.config["RECCO_API_BASE"]

    def _headers(self) -> dict:
        headers = {"Accept": "application/json"}
        key = current_app.config.get("RECCO_API_KEY")
        if key:
            headers["Authorization"] = f"Bearer {key}"
        return headers

    def get(self, endpoint: str, params: dict = None) -> dict | list | None:
        url = f"{self._base()}{endpoint}"
        try:
            resp = requests.get(url, headers=self._headers(), params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError:
            logger.error("ReccoBeats HTTP %s em %s: %s", resp.status_code, url, resp.text)
        except requests.exceptions.RequestException as e:
            logger.error("Erro de conexão com ReccoBeats: %s", e)
        return None
