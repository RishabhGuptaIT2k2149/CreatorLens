from __future__ import annotations

import time
from datetime import datetime

from config import settings
from db.database import SessionLocal, init_db
from db.models import BrandMention, Channel, IngestionJob, SponsorshipSegment, Video
from services.chunker import chunk_transcript
from services.extractor import extract_brands
from services.sponsorship import detect_sponsorships
from services.transcriber import TRANSCRIPTS_DIR, transcribe_video
from services.vector_store import upsert_chunks
from services.youtube import list_video_ids, resolve_channel


def _run_extraction(db, vid_id: str, transcript: str) -> None:
    """Run brand extraction + sponsorship detection and persist results."""
    time.sleep(settings.RATE_LIMIT_DELAY_SEC)
    try:
        mentions = extract_brands(transcript, vid_id)
        db.query(BrandMention).filter_by(video_id=vid_id).delete()
        for m in mentions:
            db.add(BrandMention(**m))
        db.commit()
        print(f"  [ok] {len(mentions)} brand mentions")
    except Exception as exc:
        print(f"  [warn] brand extraction failed: {exc}")

    time.sleep(settings.RATE_LIMIT_DELAY_SEC)
    try:
        segments = detect_sponsorships(transcript, vid_id)
        db.query(SponsorshipSegment).filter_by(video_id=vid_id).delete()
        for s in segments:
            db.add(SponsorshipSegment(**s))
        db.commit()
        if segments:
            print(f"  [ok] {len(segments)} sponsorship segments")
    except Exception as exc:
        print(f"  [warn] sponsorship detection failed: {exc}")


def run_ingestion(channel_url: str, job_id: int | None = None, max_videos: int | None = None) -> dict:
    """
    Full ingestion pipeline for a channel.

    1. Resolve channel metadata → upsert Channel row
    2. List up to MAX_VIDEOS_PER_CHANNEL video IDs
    3. For each video: transcribe → chunk → embed → upsert to ChromaDB
    4. Update IngestionJob progress throughout

    Returns a summary dict.
    """
    init_db()
    db = SessionLocal()

    try:
        # ── 1. Resolve channel ──────────────────────────────────────────────
        print(f"[worker] Resolving channel: {channel_url}")
        ch_meta = resolve_channel(channel_url)
        channel_id = ch_meta["channel_id"]

        channel = db.query(Channel).filter_by(yt_channel_id=channel_id).first()
        if channel is None:
            channel = Channel(
                yt_channel_id=channel_id,
                title=ch_meta["title"],
                subscriber_count=ch_meta["subscriber_count"],
                video_count=ch_meta["video_count"],
                uploads_playlist_id=ch_meta["uploads_playlist_id"],
            )
            db.add(channel)
            db.commit()
            db.refresh(channel)
        else:
            channel.subscriber_count = ch_meta["subscriber_count"]
            channel.video_count = ch_meta["video_count"]
            db.commit()

        print(f"[worker] Channel: {channel.title} ({channel_id})")

        # ── 2. Create or retrieve IngestionJob ──────────────────────────────
        if job_id is None:
            job = IngestionJob(channel_id=channel.id, status="running")
            db.add(job)
            db.commit()
            db.refresh(job)
        else:
            job = db.query(IngestionJob).filter_by(id=job_id).first()
            job.status = "running"
            db.commit()

        # ── 3. List videos ──────────────────────────────────────────────────
        max_videos = max_videos or settings.MAX_VIDEOS_PER_CHANNEL
        print(f"[worker] Listing up to {max_videos} videos…")
        video_items = list_video_ids(ch_meta["uploads_playlist_id"], max_videos)
        job.total = len(video_items)
        db.commit()
        print(f"[worker] Found {job.total} videos to process")

        # ── 4. Per-video: transcribe → chunk → embed → upsert ──────────────
        for idx, item in enumerate(video_items):
            vid_id = item["video_id"]
            print(f"\n[worker] [{idx+1}/{job.total}] {vid_id} — {item['title'][:60]}")

            # Upsert Video row (idempotent)
            video_row = db.query(Video).filter_by(video_id=vid_id).first()
            if video_row is None:
                video_row = Video(
                    video_id=vid_id,
                    channel_id=channel.id,
                    title=item["title"],
                    published_at=item.get("published_at") or "",
                    transcription_status="pending",
                )
                db.add(video_row)
                db.commit()
                db.refresh(video_row)

            # Case 1: fully processed — skip entirely
            if video_row.transcription_status == "ok" and video_row.extraction_done:
                print(f"  [skip] already processed")
                job.progress = idx + 1
                db.commit()
                continue

            # Case 2: transcribed but extraction not done — load from disk, skip Gemini transcription
            if video_row.transcription_status == "ok" and not video_row.extraction_done:
                transcript_path = TRANSCRIPTS_DIR / f"{vid_id}.txt"
                if transcript_path.exists():
                    transcript_text = transcript_path.read_text(encoding="utf-8")
                    _run_extraction(db, vid_id, transcript_text)
                    video_row.extraction_done = True
                    db.commit()
                    print(f"  [ok] extraction backfilled from saved transcript")
                else:
                    print(f"  [warn] transcript file missing, re-transcribing")
                    video_row.transcription_status = "pending"
                    db.commit()

                if video_row.transcription_status == "ok":
                    job.progress = idx + 1
                    db.commit()
                    continue

            # Case 3: not yet transcribed — full pipeline
            result = transcribe_video(vid_id, save_to_disk=True)
            if result["status"] == "ok":
                video_row.transcription_status = "ok"
                video_row.word_count = result["word_count"]
            elif result["status"] == "no_speech":
                video_row.transcription_status = "no_speech"
                video_row.word_count = 0
            # "error" → leave as "pending" so next run retries
            db.commit()

            if result["status"] != "ok":
                print(f"  [skip] transcription status: {result['status']} — {result.get('error', '')}")
                video_row.transcription_status = "pending"
                job.progress = idx + 1
                db.commit()
                time.sleep(settings.RATE_LIMIT_DELAY_SEC)
                continue

            # Chunk + embed + upsert
            chunks = chunk_transcript(result["transcript"], vid_id)
            upsert_chunks(channel_id, chunks)
            print(f"  [ok] {result['word_count']} words → {len(chunks)} chunks ingested")

            job.progress = idx + 1
            db.commit()

            _run_extraction(db, vid_id, result["transcript"])
            video_row.extraction_done = True
            db.commit()

        # ── 5. Finalise ─────────────────────────────────────────────────────
        channel.ingested_at = datetime.utcnow()
        job.status = "done"
        job.completed_at = datetime.utcnow()
        db.commit()

        summary = {
            "channel_id": channel_id,
            "channel_title": channel.title,
            "videos_processed": job.progress,
            "videos_total": job.total,
            "job_id": job.id,
            "status": "done",
        }
        print(f"\n[worker] Done. {summary}")
        return summary

    except Exception as exc:
        if "job" in dir():
            job.status = "error"
            job.error = str(exc)
            db.commit()
        raise
    finally:
        db.close()
