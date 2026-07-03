# Health check endpoints
from fastapi import APIRouter, status, Depends
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from app.db.session import get_redis
from app.core.cache_service import CacheService

router = APIRouter(prefix="/health", tags=["Health"])

class HealthResponse(BaseModel):
    status: str
    version: str
    checks: dict

@router.get("", response_model=HealthResponse, status_code=status.HTTP_200_OK)
@router.get("/", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check():
    """
    Базовая проверка здоровья сервиса.
    В будущем добавим проверки БД, Redis, GigaChat API.
    """
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        checks={
            "api": "ok",
            "gigachat": "pending",  # Добавим на следующем шаге
            "database": "pending",
            "redis": "pending"
        }
    )

@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """
    Проверка готовности принимать трафик (для Kubernetes).
    """
    return {"status": "ready"}

@router.get("/cache-stats", status_code=status.HTTP_200_OK)
async def cache_stats(redis_client = Depends(get_redis)):
    """
    Статистика кэша (для админ-панели).
    """
    if not redis_client:
        return {"error": "Redis not available"}
    
    cache_service = CacheService(redis_client)
    stats = await cache_service.get_stats()
    
    return {
        "cache_enabled": True,
        "stats": stats
    }

@router.post("/cache-clear", status_code=status.HTTP_200_OK)
async def cache_clear(redis_client = Depends(get_redis)):
    """
    Очистка кэша (для админ-панели).
    """
    if not redis_client:
        return {"error": "Redis not available"}
    
    cache_service = CacheService(redis_client)
    success = await cache_service.clear_all()
    
    return {
        "success": success,
        "message": "Cache cleared" if success else "Failed to clear cache"
    }
