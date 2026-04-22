from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from google import genai
from google.genai import types
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import settings
from db.database import SessionLocal, init_db
from db.models import Channel
from services.vector_store import query as vs_query

router = APIRouter(tags=["chat"])

_client: genai.Client | None = None

RAG_PROMPT = """You are an AI assistant with deep knowledge of a YouTube creator's content.
Answer the user's question using ONLY the transcript excerpts provided below.

Creator: {channel_title}

Transcript excerpts:
{context}

---
Question: {question}

Instructions:
- Answer based only on the excerpts above.
- Be specific and reference details from the transcripts.
- If the excerpts don't contain enough information to answer, say so clearly.
- Keep your answer concise (2-4 sentences unless more detail is needed).
"""


def get_db():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


class ChatRequest(BaseModel):
    question: str
    history: list[dict] = []


class SourceItem(BaseModel):
    video_id: str
    chunk_index: int
    distance: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]


@router.post("/channel/{channel_id}/chat", response_model=ChatResponse)
def chat(channel_id: str, req: ChatRequest, db: Session = Depends(get_db)):
    channel = db.query(Channel).filter_by(yt_channel_id=channel_id).first()
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Retrieve top-5 relevant chunks from ChromaDB
    chunks = vs_query(channel_id, req.question, k=5)
    if not chunks:
        return ChatResponse(
            answer="I don't have enough transcript data for this channel yet. Try ingesting more videos first.",
            sources=[],
        )

    context = "\n\n".join(
        f"[Video {c['video_id']}, chunk {c['chunk_index']}]:\n{c['chunk_text']}"
        for c in chunks
    )

    prompt = RAG_PROMPT.format(
        channel_title=channel.title,
        context=context,
        question=req.question,
    )

    client = _get_client()
    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=types.Content(parts=[types.Part(text=prompt)]),
        )
        answer = (response.text or "").strip()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini error: {exc}")

    sources = [
        SourceItem(
            video_id=c["video_id"],
            chunk_index=c["chunk_index"],
            distance=c["distance"],
        )
        for c in chunks
    ]

    return ChatResponse(answer=answer, sources=sources)