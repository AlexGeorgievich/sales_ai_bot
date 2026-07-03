# Database session setup
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from redis.asyncio import Redis
from typing import AsyncGenerator

from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()

# PostgreSQL engine with SQLite fallback for import safety and testing
db_url = settings.DATABASE_URL or "sqlite+aiosqlite:///:memory:"
engine_kwargs = {}
if "sqlite" not in db_url:
    engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 10,
        "pool_pre_ping": True,
    })

engine = create_async_engine(
    db_url,
    echo=settings.DEBUG,
    **engine_kwargs
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Redis client
redis_client: Redis = None


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy."""
    pass


async def init_db() -> None:
    """Инициализация базы данных при старте приложения."""
    global redis_client
    
    # Создаем таблицы в PostgreSQL
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("PostgreSQL tables created")
    
    # Инициализируем Redis
    redis_client = Redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    
    # Проверяем подключение к Redis
    try:
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error("Redis connection failed", error=str(e))
        raise


async def close_db() -> None:
    """Закрытие подключений к БД при остановке приложения."""
    global redis_client
    
    await engine.dispose()
    logger.info("PostgreSQL connection closed")
    
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения сессии БД.
    Используется в FastAPI через Depends().
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_redis() -> Redis:
    """Dependency для получения Redis клиента."""
    return redis_client
    