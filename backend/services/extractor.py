from __future__ import annotations

import json
import re

from google import genai
from google.genai import types

from config import settings

_client: genai.Client | None = None

EXTRACT_PROMPT = """Analyze this YouTube video transcript and extract every brand or product mention.

Return a JSON array (and nothing else) where each element has:
  "name"         – brand or product name, e.g. "NordVPN", "iPhone 15 Pro", "JBL"
  "category"     – one of: tech, software, food, clothing, automotive, finance, health, entertainment, other
  "mention_type" – one of: organic (naturally mentioned), sponsored (paid promotion), comparison (vs another product)
  "sentiment"    – one of: positive, neutral, negative
  "context"      – the exact sentence where the brand appears (max 200 chars)

Rules:
- Skip the YouTube platform itself and the creator's own channel name.
- Each distinct mention = one entry (same brand can appear multiple times with different context).
- Output ONLY the JSON array. No markdown fences, no prose.

Transcript:
{transcript}"""


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def _parse_json_array(text: str) -> list:
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`")
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return []
    return json.loads(match.group())


def extract_brands(transcript: str, video_id: str) -> list[dict]:
    """
    Extract brand/product mentions from a transcript via Gemini.
    Returns list of dicts ready to be stored as BrandMention rows.
    """
    if not transcript.strip():
        return []

    client = _get_client()
    prompt = EXTRACT_PROMPT.format(transcript=transcript[:8000])

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=types.Content(parts=[types.Part(text=prompt)]),
        )
        items = _parse_json_array(response.text or "")
    except Exception:
        return []

    results = []
    for item in items:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        results.append({
            "video_id": video_id,
            "name": str(item.get("name", ""))[:256],
            "category": str(item.get("category", "other"))[:64],
            "mention_type": str(item.get("mention_type", "organic"))[:32],
            "sentiment": str(item.get("sentiment", "neutral"))[:16],
            "context": str(item.get("context", ""))[:512],
        })
    return results