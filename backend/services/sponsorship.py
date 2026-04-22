from __future__ import annotations

import json
import re

from google import genai
from google.genai import types

from config import settings

_client: genai.Client | None = None

SPONSOR_KEYWORDS = [
    "sponsored by", "thanks to our sponsor", "use code", "use my code",
    "link in my description", "link in description", "brought to you by",
    "discount code", "promo code", "affiliate", "check out", "partner with",
    "nordvpn", "squarespace", "skillshare", "expressvpn", "manscaped",
    "hellofresh", "betterhelp", "brilliant", "curiositystream",
]

SPONSOR_PROMPT = """Analyze this YouTube video transcript to detect paid sponsorship segments.

Return a JSON array (and nothing else) where each element has:
  "sponsor_name" – name of the sponsoring brand
  "confidence"   – float from 0.0 to 1.0
  "evidence"     – the exact transcript passage that indicates sponsorship (max 300 chars)

If no paid sponsorships are found, return: []
Output ONLY the JSON array. No markdown, no prose.

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


def _heuristic_match(transcript: str) -> bool:
    lower = transcript.lower()
    return any(kw in lower for kw in SPONSOR_KEYWORDS)


def detect_sponsorships(transcript: str, video_id: str) -> list[dict]:
    """
    Detect sponsorship segments in a transcript.
    Runs a keyword heuristic first; only calls Gemini if keywords are found.
    Returns list of dicts ready to be stored as SponsorshipSegment rows.
    """
    if not transcript.strip() or not _heuristic_match(transcript):
        return []

    client = _get_client()
    prompt = SPONSOR_PROMPT.format(transcript=transcript[:8000])

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
        if not isinstance(item, dict) or not item.get("sponsor_name"):
            continue
        results.append({
            "video_id": video_id,
            "sponsor_name": str(item.get("sponsor_name", ""))[:256],
            "confidence": float(item.get("confidence", 0.5)),
            "evidence": str(item.get("evidence", ""))[:512],
            "detection_method": "llm",
        })
    return results