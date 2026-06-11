"""Database engine and session configuration.

Supports both synchronous and asynchronous database operations
for compatibility with FastAPI's async nature.
"""

from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.common.config import get_settings

settings = get_settings()


def _is_async_url(url: str) -> bool:
    """Check if database URL is configured for async driver."""
    return url.startswith(("postgresql+asyncpg://", "postgresql+aiopg://"))


# Synchronous engine (for Alembic migrations and sync operations)
sync_engine = create_engine(
    settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    if _is_async_url(settings.database_url)
    else settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.debug,
)

SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Asynchronous engine (for FastAPI async operations)
if _is_async_url(settings.database_url):
    async_engine = create_async_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        echo=settings.debug,
        pool_pre_ping=True,
    )
else:
    # Convert sync URL to async URL
    async_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    async_engine = create_async_engine(
        async_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        echo=settings.debug,
        pool_pre_ping=True,
    )

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


def get_db() -> SyncSessionLocal:
    """Dependency that provides a synchronous database session.

    Use this for synchronous endpoints and Alembic migrations.
    """
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an asynchronous database session.

    Use this for async FastAPI endpoints.
    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_async_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables (development only)."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections on shutdown."""
    await async_engine.dispose()