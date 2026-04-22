from __future__ import annotations

import re

TARGET_WORDS = 250
OVERLAP_WORDS = 20
MAX_PARA_WORDS = 400  # paragraphs longer than this get split at sentence boundaries


def _split_into_units(transcript: str) -> list[str]:
    """
    Return a list of text units (paragraphs or sentences) to accumulate into chunks.
    - Primary: split on \\n\\n (Gemini adds these at topic shifts).
    - Fallback: if a unit exceeds MAX_PARA_WORDS, split it at sentence boundaries.
    """
    raw_paras = [p.strip() for p in transcript.split("\n\n") if p.strip()]

    units: list[str] = []
    for para in raw_paras:
        if len(para.split()) <= MAX_PARA_WORDS:
            units.append(para)
        else:
            # Split long paragraphs at sentence boundaries: ". ", "! ", "? " + capital
            sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", para)
            units.extend(s.strip() for s in sentences if s.strip())

    return units


def chunk_transcript(transcript: str, video_id: str) -> list[dict]:
    """
    Split a transcript into overlapping chunks.

    Returns a list of dicts: {chunk_text, video_id, chunk_index, word_count}
    """
    units = _split_into_units(transcript)

    chunks: list[dict] = []
    buffer: list[str] = []
    overlap: list[str] = []

    for unit in units:
        buffer.extend(unit.split())

        if len(buffer) >= TARGET_WORDS:
            text = " ".join(overlap + buffer)
            chunks.append(
                {
                    "chunk_text": text,
                    "video_id": video_id,
                    "chunk_index": len(chunks),
                    "word_count": len(text.split()),
                }
            )
            overlap = buffer[-OVERLAP_WORDS:]
            buffer = []

    if buffer:
        text = " ".join(overlap + buffer)
        chunks.append(
            {
                "chunk_text": text,
                "video_id": video_id,
                "chunk_index": len(chunks),
                "word_count": len(text.split()),
            }
        )

    return chunks
