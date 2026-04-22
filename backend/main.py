from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import analyse, channel, chat, debug
from config import settings

settings.validate()

app = FastAPI(title="CreatorLens API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(channel.router)
app.include_router(analyse.router)
app.include_router(chat.router)
app.include_router(debug.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "CreatorLens API"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "youtube_key_loaded": bool(settings.YOUTUBE_API_KEY),
        "gemini_key_loaded": bool(settings.GEMINI_API_KEY),
        "gemini_model": settings.GEMINI_MODEL,
        "max_videos_per_channel": settings.MAX_VIDEOS_PER_CHANNEL,
    }