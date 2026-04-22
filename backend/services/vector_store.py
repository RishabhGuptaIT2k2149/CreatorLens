from __future__ import annotations

from pathlib import Path

import chromadb

from config import settings
from services.embedder import embed

_client: chromadb.PersistentClient | None = None


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        persist_dir = Path(settings.CHROMA_PERSIST_DIR)
        persist_dir.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(persist_dir))
    return _client


def _collection_name(channel_id: str) -> str:
    # ChromaDB collection names must be alphanumeric + hyphens, 3-63 chars
    safe = "".join(c if c.isalnum() else "-" for c in channel_id)
    return f"ch-{safe}"[:63]


def upsert_chunks(channel_id: str, chunks: list[dict]) -> None:
    """
    Embed and upsert chunks into the channel's ChromaDB collection.

    Each chunk dict must have: chunk_text, video_id, chunk_index
    Optional keys are stored as metadata as-is.
    """
    if not chunks:
        return

    client = _get_client()
    collection = client.get_or_create_collection(
        name=_collection_name(channel_id),
        metadata={"hnsw:space": "cosine"},
    )

    texts = [c["chunk_text"] for c in chunks]
    embeddings = embed(texts)

    ids = [f"{c['video_id']}__{c['chunk_index']}" for c in chunks]
    metadatas = [
        {
            "video_id": c["video_id"],
            "chunk_index": c["chunk_index"],
            "word_count": c.get("word_count", len(c["chunk_text"].split())),
        }
        for c in chunks
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )


def query(channel_id: str, query_text: str, k: int = 5) -> list[dict]:
    """
    Return the top-k most similar chunks for the given query.
    Each result: {chunk_text, video_id, chunk_index, distance}
    """
    client = _get_client()
    try:
        collection = client.get_collection(name=_collection_name(channel_id))
    except Exception:
        return []

    query_embedding = embed([query_text])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    out = []
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]
    for doc, meta, dist in zip(docs, metas, dists):
        out.append(
            {
                "chunk_text": doc,
                "video_id": meta["video_id"],
                "chunk_index": meta["chunk_index"],
                "distance": round(dist, 4),
            }
        )
    return out


def collection_count(channel_id: str) -> int:
    """Return total number of chunks stored for this channel."""
    client = _get_client()
    try:
        col = client.get_collection(name=_collection_name(channel_id))
        return col.count()
    except Exception:
        return 0
