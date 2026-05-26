"""
Database engine and session management.

Uses async SQLAlchemy with PostgreSQL (via asyncpg driver).
Supabase PostgreSQL is fully compatible with SQLAlchemy.
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create async engine for PostgreSQL
# pool_pre_ping=True ensures connections are valid before use (important for serverless DBs like Supabase)
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL queries in debug mode
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={
        "ssl": True,  # Supabase requires SSL connections
    },
)

# Session factory: creates async sessions bound to the engine
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevent expired object errors after commit
    autoflush=False,
)

# Base class for all ORM models
Base = declarative_base()


async def init_db(max_retries: int = 5, base_delay: float = 1.0):
    """
    Initialize database tables with retry logic.

    In production with multiple workers, use Alembic migrations instead.
    This function is useful for quick local setup and testing.
    """
    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables initialized successfully.")
            return
        except OSError as e:
            last_exception = e
            logger.warning(
                "Database connection attempt %d/%d failed: %s",
                attempt,
                max_retries,
                e,
            )
            if attempt < max_retries:
                wait = base_delay * (2 ** (attempt - 1))
                logger.info("Retrying in %.1f seconds...", wait)
                await asyncio.sleep(wait)
            else:
                logger.error("All database connection attempts exhausted.")
                raise last_exception


async def close_db():
    """Dispose the database engine. Call on application shutdown."""
    await engine.dispose()


async def get_session() -> AsyncSession:
    """
    Dependency for FastAPI endpoints that need a database session.

    Usage:
        @app.get("/users")
        async def list_users(session: AsyncSession = Depends(get_session)):
            ...
    """
    async with AsyncSessionLocal() as session:
        yield session
