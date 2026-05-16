"""
StockAnalist Database Configuration
Async PostgreSQL connection using SQLAlchemy 2.0
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from app.core.config import settings


_async_engine_kwargs = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True,
}

if settings.ENVIRONMENT.lower() == "test":
    # TestClient and ASGITransport can exercise the app on different event loops.
    # asyncpg pooled connections are loop-bound, so tests use one-shot
    # connections while production keeps the normal pool below.
    _async_engine_kwargs["poolclass"] = NullPool
else:
    _async_engine_kwargs.update(
        pool_size=20,
        max_overflow=10,
    )

# Async engine for FastAPI
async_engine = create_async_engine(
    settings.DATABASE_URL,
    **_async_engine_kwargs,
)

# Sync engine for Alembic migrations and data collection scripts
sync_engine = create_engine(
    settings.DATABASE_SYNC_URL,
    echo=False,
    pool_size=5,
    max_overflow=5,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency for FastAPI route handlers."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables (for development only)."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections."""
    await async_engine.dispose()
