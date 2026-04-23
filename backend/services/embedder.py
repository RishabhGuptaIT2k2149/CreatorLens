from __future__ import annotations

import requests

from config import settings

_BASE = "https://generativelanguage.googleapis.com/v1/models/text-embedding-004:embedContent"


def embed(texts: list[str]) -> list[list[float]]:
    """
    Return 768-dim embeddings via Gemini text-embedding-004 REST API (v1).
    Calls the endpoint directly to avoid the SDK's v1beta limitation.
    """
    results = []
    for text in texts:
        response = requests.post(
            _BASE,
            params={"key": settings.GEMINI_API_KEY},
            json={"content": {"parts": [{"text": text}]}},
            timeout=30,
        )
        response.raise_for_status()
        results.append(response.json()["embedding"]["values"])
    return results