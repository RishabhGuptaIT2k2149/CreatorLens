from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from config import settings
from services import youtube

router = APIRouter(prefix="/channel", tags=["channel"])


class ChannelInfo(BaseModel):
    channel_id: str
    title: str
    subscriber_count: int
    video_count: int
    uploads_playlist_id: str


class VideoItem(BaseModel):
    video_id: str
    title: str
    published_at: str | None = None


class VideoListResponse(BaseModel):
    channel_id: str
    channel_title: str
    total_on_channel: int
    videos_returned: int
    videos: list[VideoItem]


@router.get("/info", response_model=ChannelInfo)
def channel_info(url: str = Query(..., description="YouTube channel URL")):
    try:
        info = youtube.resolve_channel(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ChannelInfo(
        channel_id=info["channel_id"],
        title=info["title"],
        subscriber_count=info["subscriber_count"],
        video_count=info["video_count"],
        uploads_playlist_id=info["uploads_playlist_id"],
    )


@router.get("/videos", response_model=VideoListResponse)
def channel_videos(
    url: str = Query(..., description="YouTube channel URL"),
    limit: int | None = Query(
        default=None,
        ge=1,
        le=500,
        description=f"Max videos (defaults to MAX_VIDEOS_PER_CHANNEL={settings.MAX_VIDEOS_PER_CHANNEL})",
    ),
):
    try:
        info = youtube.resolve_channel(url)
        cap = limit or settings.MAX_VIDEOS_PER_CHANNEL
        videos = youtube.list_video_ids(info["uploads_playlist_id"], cap)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return VideoListResponse(
        channel_id=info["channel_id"],
        channel_title=info["title"],
        total_on_channel=info["video_count"],
        videos_returned=len(videos),
        videos=[VideoItem(**v) for v in videos],
    )