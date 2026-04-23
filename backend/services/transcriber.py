import time
from pathlib import Path

from google import genai
from google.genai import types

from config import settings

_client: genai.Client | None = None

import os
_default_transcripts = Path(__file__).resolve().parent.parent / "transcripts"
TRANSCRIPTS_DIR = Path(os.getenv("TRANSCRIPTS_DIR", str(_default_transcripts)))
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

PROMPT = """Transcribe this YouTube video into clean, readable text.

Rules:
- Output the spoken content verbatim. Do NOT summarize or paraphrase.
- Do NOT include timecodes, speaker labels, or tags like [music] / [applause].
- Preserve sentence boundaries. Insert a paragraph break when the topic shifts.
- If the video contains no intelligible speech (music-only, unintelligible audio, silence),
  output exactly this single token and nothing else: NO_SPEECH
"""


def _client_singleton() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def transcribe_video(video_id: str, save_to_disk: bool = True) -> dict:
    """
    Transcribe a single YouTube video by ID.
    Returns:
      {
        'video_id', 'status' ('ok'|'no_speech'|'error'),
        'transcript' (str), 'char_count', 'word_count',
        'elapsed_sec', 'saved_path' (str|None), 'error' (str|None)
      }
    """
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    client = _client_singleton()

    started = time.time()
    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=types.Content(
                parts=[
                    types.Part(file_data=types.FileData(file_uri=video_url)),
                    types.Part(text=PROMPT),
                ]
            ),
        )
        text = (response.text or "").strip()
    except Exception as e:  # noqa: BLE001  — surface full error upstream
        return {
            "video_id": video_id,
            "status": "error",
            "transcript": "",
            "char_count": 0,
            "word_count": 0,
            "elapsed_sec": round(time.time() - started, 2),
            "saved_path": None,
            "error": f"{type(e).__name__}: {e}",
        }

    elapsed = round(time.time() - started, 2)

    if not text or text == "NO_SPEECH":
        return {
            "video_id": video_id,
            "status": "no_speech",
            "transcript": "",
            "char_count": 0,
            "word_count": 0,
            "elapsed_sec": elapsed,
            "saved_path": None,
            "error": None,
        }

    saved_path = None
    if save_to_disk:
        out_path = TRANSCRIPTS_DIR / f"{video_id}.txt"
        out_path.write_text(text, encoding="utf-8")
        saved_path = str(out_path)

    return {
        "video_id": video_id,
        "status": "ok",
        "transcript": text,
        "char_count": len(text),
        "word_count": len(text.split()),
        "elapsed_sec": elapsed,
        "saved_path": saved_path,
        "error": None,
    }
