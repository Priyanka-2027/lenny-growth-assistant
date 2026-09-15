"""
Async SQLAlchemy engine + session factory.
Call init_db() on startup to create all tables.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

from sqlalchemy import event
from sqlalchemy.pool import StaticPool

def _get_engine_kwargs(url: str) -> dict:
    """Return engine kwargs appropriate for the database dialect."""
    if url.startswith("sqlite"):
        return {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }
    return {
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
    }

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    **_get_engine_kwargs(settings.database_url),
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def init_db() -> None:
    """Create all tables if they don't exist."""
    from app.db.base import Base
    import app.db.models  # noqa: F401 — ensure models are registered

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("db_tables_created_or_verified")
    except Exception as exc:
        logger.error("db_init_failed", error=str(exc))
        raise


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields a DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
