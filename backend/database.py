import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv

load_dotenv()


def _get_database_url() -> str:
    """Return the SQLAlchemy connection string with sensible fallbacks."""

    database_url = (
        os.getenv("SQLALCHEMY_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or "postgresql://tradingbotuser@localhost/tradingbotdb"
    )

    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    return database_url


SQLALCHEMY_DATABASE_URL = _get_database_url()
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


logger = logging.getLogger(__name__)


def init_db() -> None:
    """Create database tables if they do not already exist."""

    # Importing models ensures SQLAlchemy is aware of all table metadata before
    # issuing ``create_all``. The import is local to avoid circular imports when
    # ``models`` imports ``Base`` from this module.
    import models  # noqa: F401

    if not Base.metadata.tables:
        logger.warning(
            "No SQLAlchemy models registered with metadata; skipping auto-create."
        )
        return

    Base.metadata.create_all(bind=engine, checkfirst=True)
    logger.debug("Database tables checked/created successfully")
