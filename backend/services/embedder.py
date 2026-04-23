from __future__ import annotations

import requests

from config import settings

_BASE = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"


def embed(texts: list[str]) -> list[list[float]]:
    results = []
    for text in texts:
        response = requests.post(
            _BASE,
            params={"key": settings.GEMINI_API_KEY},
            json={"content": {"parts": [{"text": text}]}},
            timeout=30,
        )
        if not response.ok:
            raise RuntimeError(f"Embedding API error {response.status_code}: {response.text[:200]}")
        results.append(response.json()["embedding"]["values"])
    return results