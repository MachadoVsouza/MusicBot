"""
recco_beats.py — Integração com a API da ReccoBeats
Substitui o audio_features depreciado do Spotify.

Fluxo:
  1. Recebe o spotify_id da track
  2. GET /v1/track?ids={spotify_id}  → obtém o reccobeats_id (UUID)
  3. GET /v1/track/{reccobeats_id}/audio-features → retorna os dados de áudio
"""

import os
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RECCO_API_BASE = "https://api.reccobeats.com/v1"

# A ReccoBeats é gratuita e não exige API key nos endpoints públicos.
# Se você tiver uma chave, defina a variável de ambiente RECCO_API_KEY.
RECCO_API_KEY = os.getenv("RECCO_API_KEY", None)


def _headers():
    h = {"Accept": "application/json"}
    if RECCO_API_KEY:
        h["Authorization"] = f"Bearer {RECCO_API_KEY}"
    return h


def _get(endpoint: str, params: dict = None):
    """Faz um GET autenticado para a ReccoBeats e devolve o JSON ou None."""
    url = f"{RECCO_API_BASE}{endpoint}"
    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"ReccoBeats HTTP {resp.status_code} em {url}: {resp.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de conexão com ReccoBeats: {e}")
    return None


# ── Busca o reccobeats_id a partir do spotify_id ──────────────────────────────

def get_reccobeats_id(spotify_id: str) -> str | None:
    """
    Dado um Spotify Track ID, devolve o ID interno da ReccoBeats (UUID v4).
    O endpoint /v1/track aceita tanto ReccoBeats IDs quanto Spotify IDs como ?ids=
    """
    if not spotify_id:
        return None

    data = _get("/track", params={"ids": spotify_id})

    # A resposta é uma lista de objetos track
    if isinstance(data, list) and len(data) > 0:
        return data[0].get("id")

    # Alguns endpoints devolvem { "content": [...] }
    if isinstance(data, dict):
        items = data.get("content") or data.get("items") or data.get("tracks") or []
        if items:
            return items[0].get("id")

    logger.warning(f"Não foi possível mapear spotify_id '{spotify_id}' para reccobeats_id.")
    return None


# ── Audio features ─────────────────────────────────────────────────────────────

def get_audio_features_by_reccobeats_id(reccobeats_id: str) -> dict | None:
    """Obtém as audio features usando o ID interno da ReccoBeats."""
    if not reccobeats_id:
        return None
    return _get(f"/track/{reccobeats_id}/audio-features")


def get_audio_features(spotify_id: str) -> dict | None:
    """
    Função principal — recebe um Spotify Track ID e devolve as audio features.

    Uso em functions.py:
        from recco_beats import get_audio_features
        features = get_audio_features(track_id)
    """
    reccobeats_id = get_reccobeats_id(spotify_id)
    if not reccobeats_id:
        logger.error(f"Track '{spotify_id}' não encontrada na ReccoBeats.")
        return None

    features = get_audio_features_by_reccobeats_id(reccobeats_id)
    if features:
        # Anexa o spotify_id para facilitar o rastreamento
        features["spotify_id"] = spotify_id
        features["reccobeats_id"] = reccobeats_id

    return features


# ── Recomendações (bônus) ──────────────────────────────────────────────────────

def get_recommendations(seed_ids: list[str], size: int = 10) -> list[dict]:
    """
    Retorna recomendações baseadas em uma lista de Spotify IDs ou ReccoBeats IDs.
    Mistura dos dois tipos é aceita.
    """
    if not seed_ids:
        return []

    params = [("seeds", sid) for sid in seed_ids] + [("size", size)]
    data = _get("/track/recommendation", params=params)

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("content") or data.get("tracks") or []
    return []