from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# Resolve database path inside the project directory
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "time_tracker.db"


class Base(DeclarativeBase):
    pass


# SQLite engine; check_same_thread disabled for FastAPI workers
engine = create_engine(
    f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


