from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    yt_channel_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(256))
    subscriber_count: Mapped[int] = mapped_column(Integer, default=0)
    video_count: Mapped[int] = mapped_column(Integer, default=0)
    uploads_playlist_id: Mapped[str] = mapped_column(String(64), default="")
    ingested_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    videos: Mapped[list[Video]] = relationship(back_populates="channel")
    jobs: Mapped[list[IngestionJob]] = relationship(back_populates="channel")


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), index=True)
    title: Mapped[str] = mapped_column(String(512), default="")
    published_at: Mapped[str] = mapped_column(String(32), default="")
    transcription_status: Mapped[str] = mapped_column(
        String(16), default="pending"
    )  # pending | ok | no_speech | error
    word_count: Mapped[int] = mapped_column(Integer, default=0)

    channel: Mapped[Channel] = relationship(back_populates="videos")


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), index=True)
    status: Mapped[str] = mapped_column(
        String(16), default="pending"
    )  # pending | running | done | error
    progress: Mapped[int] = mapped_column(Integer, default=0)   # videos done
    total: Mapped[int] = mapped_column(Integer, default=0)       # videos to process
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    channel: Mapped[Channel] = relationship(back_populates="jobs")


class BrandMention(Base):
    __tablename__ = "brand_mentions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[str] = mapped_column(String(32), index=True)  # YouTube video ID
    name: Mapped[str] = mapped_column(String(256))
    category: Mapped[str] = mapped_column(String(64), default="other")
    mention_type: Mapped[str] = mapped_column(String(32), default="organic")
    sentiment: Mapped[str] = mapped_column(String(16), default="neutral")
    context: Mapped[str] = mapped_column(Text, default="")


class SponsorshipSegment(Base):
    __tablename__ = "sponsorship_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[str] = mapped_column(String(32), index=True)  # YouTube video ID
    sponsor_name: Mapped[str] = mapped_column(String(256))
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    evidence: Mapped[str] = mapped_column(Text, default="")
    detection_method: Mapped[str] = mapped_column(String(16), default="llm")
