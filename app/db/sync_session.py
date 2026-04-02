"""Synchronous SQLAlchemy session for use inside Celery tasks.

Celery workers run in a separate process and are synchronous by default.
This module provides a plain psycopg2-backed engine so tasks can query
the database without needing an async event loop.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Strip the async driver prefix so psycopg2 is used instead of asyncpg
_sync_url = settings.DATABASE_URL.replace("+asyncpg", "")

_engine = create_engine(_sync_url, pool_pre_ping=True)
SyncSessionLocal: sessionmaker[Session] = sessionmaker(bind=_engine, expire_on_commit=False)
