from __future__ import annotations

from google import genai

from config import settings

_client: genai.Client | None = None

EMBED_MODEL = "models/embedding-001"


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def embed(texts: list[str]) -> list[list[float]]:
    """
    Return embeddings via Gemini embedding-001 (768-dim).
    Processes one text at a time — the embed API does not support batching.
    """
    client = _get_client()
    results = []
    for text in texts:
        response = client.models.embed_content(
            model=EMBED_MODEL,
            contents=text,
        )
        results.append(response.embeddings[0].values)
    return results