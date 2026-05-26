"""
Database engine and session management.

Uses async SQLAlchemy with PostgreSQL (via asyncpg driver).
Supabase PostgreSQL is fully compatible with SQLAlchemy.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.config import get_settings

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


async def init_db():
    """
    Initialize database tables.

    In production with multiple workers, use Alembic migrations instead.
    This function is useful for quick local setup and testing.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


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
