from __future__ import annotations

from google import genai

from config import settings

_client: genai.Client | None = None

EMBED_MODEL = "text-embedding-004"


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def embed(texts: list[str]) -> list[list[float]]:
    """
    Return embeddings via Gemini text-embedding-004.
    Processes in batches of 100 to stay within API limits.
    Output dimension: 768.
    """
    client = _get_client()
    results = []
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.models.embed_content(
            model=EMBED_MODEL,
            contents=batch,
        )
        results.extend(e.values for e in response.embeddings)
    return results