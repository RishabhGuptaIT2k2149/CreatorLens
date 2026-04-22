import os
from pathlib import Path
from dotenv import load_dotenv

# .env lives at the project root: creatorlens/.env
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    # API Keys
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Models
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )

    # Storage
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

    # Dev / testing
    TEST_CHANNEL_URL: str = os.getenv("TEST_CHANNEL_URL", "")

    # Limits
    MAX_VIDEOS_PER_CHANNEL: int = int(os.getenv("MAX_VIDEOS_PER_CHANNEL", "50"))
    RATE_LIMIT_DELAY_SEC: int = int(os.getenv("RATE_LIMIT_DELAY_SEC", "4"))

    # CORS
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173"
    ).split(",")

    def validate(self) -> None:
        missing = [
            k for k, v in [
                ("YOUTUBE_API_KEY", self.YOUTUBE_API_KEY),
                ("GEMINI_API_KEY", self.GEMINI_API_KEY),
            ] if not v
        ]
        if missing:
            raise RuntimeError(
                f"Missing env vars: {', '.join(missing)}. "
                f"Check your .env at {PROJECT_ROOT / '.env'}"
            )


settings = Settings()