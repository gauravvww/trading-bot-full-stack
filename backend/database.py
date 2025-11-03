"""Helpers for configuring the SQLAlchemy engine and FastAPI dependencies."""

from __future__ import annotations

import logging
import os
from typing import Iterator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

logger = logging.getLogger(__name__)


def _normalise_database_url(url: str) -> str:
    """Render provides legacy ``postgres://`` URLs—coerce them for SQLAlchemy."""

    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def _database_url() -> str:
    """Resolve the database URL from environment variables with fallbacks."""

    url = (
        os.getenv("SQLALCHEMY_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or "postgresql://tradingbotuser@localhost/tradingbotdb"
    )
    return _normalise_database_url(url)


SQLALCHEMY_DATABASE_URL = _database_url()
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def init_db() -> None:
    """Import models and create their tables if the database is reachable."""

    try:
        import models  # noqa: WPS433 - imported for side effects
    except ImportError:  # pragma: no cover - keeps startup resilient
        logger.warning("No models module found; skipping automatic table creation")
        return

    try:
        models.Base.metadata.create_all(bind=engine, checkfirst=True)
    except OperationalError as exc:
        logger.error("Unable to initialise database: %s", exc)
        raise


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a database session per request."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
