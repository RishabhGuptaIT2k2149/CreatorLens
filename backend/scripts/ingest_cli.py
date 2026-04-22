"""
CLI ingestion script.

Usage (from backend/ with venv active):
    python scripts/ingest_cli.py [CHANNEL_URL]

Defaults to TEST_CHANNEL_URL from .env.
Override MAX_VIDEOS_PER_CHANNEL at runtime:
    MAX_VIDEOS_PER_CHANNEL=3 python scripts/ingest_cli.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make sure 'backend/' is on the path when run from any working directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from services.vector_store import query
from workers.ingestion_worker import run_ingestion


def main() -> None:
    channel_url = sys.argv[1] if len(sys.argv) > 1 else settings.TEST_CHANNEL_URL
    if not channel_url:
        print("Error: pass a channel URL as the first argument or set TEST_CHANNEL_URL in .env")
        sys.exit(1)

    print("=" * 60)
    print(f"CreatorLens — ingesting: {channel_url}")
    print(f"MAX_VIDEOS_PER_CHANNEL = {settings.MAX_VIDEOS_PER_CHANNEL}")
    print("=" * 60)

    summary = run_ingestion(channel_url)

    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print(f"  Channel : {summary['channel_title']}")
    print(f"  Videos  : {summary['videos_processed']} / {summary['videos_total']}")
    print(f"  Job ID  : {summary['job_id']}")
    print("=" * 60)

    # ── Test retrieval ──────────────────────────────────────────────────────
    test_query = "phone durability test"
    print(f"\nTest retrieval: '{test_query}'")
    results = query(summary["channel_id"], test_query, k=3)
    if not results:
        print("  No results found (vector store may be empty).")
        return

    for i, r in enumerate(results, 1):
        print(
            f"\n  Result {i} — video={r['video_id']} chunk={r['chunk_index']} "
            f"dist={r['distance']}"
        )
        print(f"  {r['chunk_text'][:200]}…")


if __name__ == "__main__":
    main()
