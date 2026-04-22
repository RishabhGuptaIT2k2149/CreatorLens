from __future__ import annotations

from sentence_transformers import SentenceTransformer

from config import settings

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        model_name = settings.EMBEDDING_MODEL.replace(
            "sentence-transformers/", ""
        )
        _model = SentenceTransformer(model_name)
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    """Return 384-dim embeddings for each text. Loads the model on first call."""
    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return vectors.tolist()
