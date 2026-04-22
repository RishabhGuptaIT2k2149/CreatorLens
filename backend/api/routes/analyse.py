from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import SessionLocal, init_db
from db.models import BrandMention, Channel, IngestionJob, SponsorshipSegment, Video
from services.youtube import resolve_channel
from workers.ingestion_worker import run_ingestion

router = APIRouter(tags=["ingestion"])


def get_db():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class AnalyseRequest(BaseModel):
    channel_url: str
    max_videos: int = 5


class AnalyseResponse(BaseModel):
    job_id: int
    channel_id: str
    channel_title: str
    message: str


class StatusResponse(BaseModel):
    job_id: int
    status: str
    progress: int
    total: int
    error: str | None = None


class OverviewResponse(BaseModel):
    channel_id: str
    title: str
    subscriber_count: int
    video_count: int
    ingested_at: str | None
    videos_transcribed: int
    videos_failed: int
    videos_total_ingested: int


class BrandItem(BaseModel):
    name: str
    category: str
    total_mentions: int
    sentiment_breakdown: dict[str, int]
    mention_types: dict[str, int]
    video_ids: list[str]


class BrandsResponse(BaseModel):
    channel_id: str
    brands: list[BrandItem]


class SponsorItem(BaseModel):
    video_id: str
    sponsor_name: str
    confidence: float
    evidence: str
    detection_method: str


class SponsorsResponse(BaseModel):
    channel_id: str
    sponsors: list[SponsorItem]


@router.post("/analyse", response_model=AnalyseResponse)
def analyse(
    req: AnalyseRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        ch_meta = resolve_channel(req.channel_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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
    else:
        channel.subscriber_count = ch_meta["subscriber_count"]
        channel.video_count = ch_meta["video_count"]
    db.commit()
    db.refresh(channel)

    job = IngestionJob(channel_id=channel.id, status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(run_ingestion, req.channel_url, job.id, req.max_videos)

    return AnalyseResponse(
        job_id=job.id,
        channel_id=channel_id,
        channel_title=channel.title,
        message=f"Ingestion started. Poll /channel/{channel_id}/status for progress.",
    )


@router.get("/channel/{channel_id}/status", response_model=StatusResponse)
def channel_status(channel_id: str, db: Session = Depends(get_db)):
    channel = db.query(Channel).filter_by(yt_channel_id=channel_id).first()
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    job = (
        db.query(IngestionJob)
        .filter_by(channel_id=channel.id)
        .order_by(IngestionJob.id.desc())
        .first()
    )
    if job is None:
        raise HTTPException(status_code=404, detail="No ingestion job found for this channel")

    return StatusResponse(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        total=job.total,
        error=job.error,
    )


@router.get("/channel/{channel_id}/overview", response_model=OverviewResponse)
def channel_overview(channel_id: str, db: Session = Depends(get_db)):
    channel = db.query(Channel).filter_by(yt_channel_id=channel_id).first()
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    videos = db.query(Video).filter_by(channel_id=channel.id).all()
    transcribed = sum(1 for v in videos if v.transcription_status == "ok")
    failed = sum(1 for v in videos if v.transcription_status in ("error", "no_speech"))

    return OverviewResponse(
        channel_id=channel.yt_channel_id,
        title=channel.title,
        subscriber_count=channel.subscriber_count,
        video_count=channel.video_count,
        ingested_at=channel.ingested_at.isoformat() if channel.ingested_at else None,
        videos_transcribed=transcribed,
        videos_failed=failed,
        videos_total_ingested=len(videos),
    )


@router.get("/channel/{channel_id}/brands", response_model=BrandsResponse)
def channel_brands(channel_id: str, db: Session = Depends(get_db)):
    channel = db.query(Channel).filter_by(yt_channel_id=channel_id).first()
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    video_ids = [v.video_id for v in db.query(Video).filter_by(channel_id=channel.id).all()]
    mentions = db.query(BrandMention).filter(BrandMention.video_id.in_(video_ids)).all()

    # Aggregate by brand name
    grouped: dict[str, dict] = {}
    for m in mentions:
        key = m.name.lower()
        if key not in grouped:
            grouped[key] = {
                "name": m.name,
                "category": m.category,
                "total_mentions": 0,
                "sentiment_breakdown": {"positive": 0, "neutral": 0, "negative": 0},
                "mention_types": {"organic": 0, "sponsored": 0, "comparison": 0},
                "video_ids": [],
            }
        g = grouped[key]
        g["total_mentions"] += 1
        g["sentiment_breakdown"][m.sentiment] = g["sentiment_breakdown"].get(m.sentiment, 0) + 1
        g["mention_types"][m.mention_type] = g["mention_types"].get(m.mention_type, 0) + 1
        if m.video_id not in g["video_ids"]:
            g["video_ids"].append(m.video_id)

    brands = sorted(grouped.values(), key=lambda x: x["total_mentions"], reverse=True)
    return BrandsResponse(channel_id=channel_id, brands=brands)


@router.get("/channel/{channel_id}/sponsors", response_model=SponsorsResponse)
def channel_sponsors(channel_id: str, db: Session = Depends(get_db)):
    channel = db.query(Channel).filter_by(yt_channel_id=channel_id).first()
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    video_ids = [v.video_id for v in db.query(Video).filter_by(channel_id=channel.id).all()]
    segments = (
        db.query(SponsorshipSegment)
        .filter(SponsorshipSegment.video_id.in_(video_ids))
        .order_by(SponsorshipSegment.confidence.desc())
        .all()
    )

    return SponsorsResponse(
        channel_id=channel_id,
        sponsors=[
            SponsorItem(
                video_id=s.video_id,
                sponsor_name=s.sponsor_name,
                confidence=s.confidence,
                evidence=s.evidence,
                detection_method=s.detection_method,
            )
            for s in segments
        ],
    )