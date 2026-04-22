from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services import transcriber

router = APIRouter(prefix="/debug", tags=["debug"])


class TranscribeResponse(BaseModel):
    video_id: str
    status: str
    elapsed_sec: float
    char_count: int
    word_count: int
    saved_path: str | None
    preview: str
    error: str | None = None


@router.get("/transcribe", response_model=TranscribeResponse)
def transcribe(video_id: str = Query(..., min_length=11, max_length=11)):
    result = transcriber.transcribe_video(video_id)

    if result["status"] == "error":
        raise HTTPException(status_code=502, detail=result["error"])

    return TranscribeResponse(
        video_id=result["video_id"],
        status=result["status"],
        elapsed_sec=result["elapsed_sec"],
        char_count=result["char_count"],
        word_count=result["word_count"],
        saved_path=result["saved_path"],
        preview=result["transcript"][:600],
        error=result["error"],
    )