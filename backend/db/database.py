from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DB_PATH = Path(__file__).resolve().parent.parent / "creatorlens.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Create all tables if they don't exist, then run column migrations."""
    from db import models  # noqa: F401 — import triggers table registration
    Base.metadata.create_all(bind=engine)
    _migrate()


def _migrate() -> None:
    """Add columns introduced after the initial schema was created."""
    migrations = [
        "ALTER TABLE videos ADD COLUMN extraction_done INTEGER NOT NULL DEFAULT 0",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass  # column already exists
