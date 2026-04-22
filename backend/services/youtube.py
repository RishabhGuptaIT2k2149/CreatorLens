from urllib.parse import urlparse

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import settings


def _client():
    return build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)


def _parse_channel_identifier(url: str) -> dict:
    """
    Supported URL forms:
      https://www.youtube.com/@handle
      https://www.youtube.com/channel/UCxxxx
      https://www.youtube.com/user/username
    """
    path = urlparse(url).path.strip("/")
    if not path:
        raise ValueError(f"Cannot parse channel from URL: {url}")

    if path.startswith("@"):
        return {"type": "handle", "value": path}

    parts = path.split("/")
    if parts[0] == "channel" and len(parts) > 1:
        return {"type": "id", "value": parts[1]}
    if parts[0] == "user" and len(parts) > 1:
        return {"type": "username", "value": parts[1]}

    raise ValueError(
        f"Unsupported channel URL: {url}. "
        "Use the @handle form (e.g. https://www.youtube.com/@JerryRigEverything) "
        "or the /channel/UC... form."
    )


def resolve_channel(url: str) -> dict:
    """
    Returns channel metadata + uploads playlist ID.
    API cost: 1 unit.
    """
    ident = _parse_channel_identifier(url)
    params = {"part": "snippet,contentDetails,statistics"}
    if ident["type"] == "handle":
        params["forHandle"] = ident["value"]
    elif ident["type"] == "id":
        params["id"] = ident["value"]
    elif ident["type"] == "username":
        params["forUsername"] = ident["value"]

    try:
        resp = _client().channels().list(**params).execute()
    except HttpError as e:
        raise ValueError(f"YouTube API error: {e}") from e

    items = resp.get("items", [])
    if not items:
        raise ValueError(f"No channel found for: {url}")

    ch = items[0]
    return {
        "channel_id": ch["id"],
        "title": ch["snippet"]["title"],
        "description": ch["snippet"].get("description", ""),
        "uploads_playlist_id": ch["contentDetails"]["relatedPlaylists"]["uploads"],
        "subscriber_count": int(ch["statistics"].get("subscriberCount", 0)),
        "video_count": int(ch["statistics"].get("videoCount", 0)),
    }


def list_video_ids(uploads_playlist_id: str, max_videos: int) -> list[dict]:
    """
    Returns [{'video_id', 'title', 'published_at'}], newest first.
    API cost: 1 unit per page of up to 50 videos.
    """
    yt = _client()
    videos: list[dict] = []
    page_token = None

    while len(videos) < max_videos:
        page_size = min(50, max_videos - len(videos))
        try:
            resp = yt.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=page_size,
                pageToken=page_token,
            ).execute()
        except HttpError as e:
            raise ValueError(f"YouTube API error listing videos: {e}") from e

        for item in resp.get("items", []):
            videos.append({
                "video_id": item["contentDetails"]["videoId"],
                "title": item["snippet"]["title"],
                "published_at": item["contentDetails"].get("videoPublishedAt"),
            })

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return videos[:max_videos]