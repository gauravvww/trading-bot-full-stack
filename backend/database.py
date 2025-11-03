"""Database configuration helpers used by the FastAPI service."""

from __future__ import annotations

import importlib
import logging
import os
import pkgutil
from types import ModuleType
from typing import Iterable, Iterator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

logger = logging.getLogger(__name__)


def _normalize_database_url(url: str) -> str:
    """Normalise legacy prefixes so SQLAlchemy can open the connection."""

    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def get_database_url() -> str:
    """Return the SQLAlchemy connection string with sensible fallbacks."""

    url = (
        os.getenv("SQLALCHEMY_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or "postgresql://tradingbotuser@localhost/tradingbotdb"
    )
    return _normalize_database_url(url)


SQLALCHEMY_DATABASE_URL = get_database_url()
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def _load_models() -> Iterable[ModuleType]:
    """Import modules that define SQLAlchemy models."""

    try:
        module = importlib.import_module("models")
    except ModuleNotFoundError as exc:  # pragma: no cover - defensive
        logger.warning("Could not import models module: %s", exc)
        return []

    # Import submodules so declarative mappings run. This is defensive—today all
    # models live in ``models.py`` but this will support future package splits.
    package_path = getattr(module, "__path__", None)
    if not package_path:
        return [module]

    submodules = []
    for finder, name, ispkg in pkgutil.walk_packages(
        package_path, prefix=f"{module.__name__}."
    ):
        submodules.append(importlib.import_module(name))
    return [module, *submodules]


def init_db() -> None:
    """Create database tables if they do not already exist."""

    _load_models()

    metadata = Base.metadata
    if not metadata.sorted_tables:
        logger.warning(
            "No SQLAlchemy models registered with metadata; skipping auto-create."
        )
        return

    metadata.create_all(bind=engine, checkfirst=True)
    logger.debug("Database tables checked/created successfully")


def get_db_session() -> Iterator[Session]:
    """Context manager-style generator used by FastAPI dependencies."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
