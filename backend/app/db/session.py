from collections.abc import AsyncGenerator
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=not settings.database_url.startswith('mysql+aiomysql://'),
    pool_recycle=1800,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
async_session_factory = AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            try:
                await session.commit()
            except Exception:
                logger.exception('database_commit_failed')
                try:
                    await session.rollback()
                except Exception:
                    logger.exception('database_rollback_failed')
                if not settings.is_local_environment:
                    raise
        except Exception:
            try:
                await session.rollback()
            except Exception:
                logger.exception('database_rollback_failed')
            raise
