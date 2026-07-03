import json
import hashlib
from typing import Optional, Any
from redis.asyncio import Redis
from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()


class CacheService:
    """
    Сервис для кэширования ответов GigaChat в Redis.
    Ускоряет ответы на типовые вопросы и снижает нагрузку на API.
    """
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.default_ttl = 3600  # 1 час по умолчанию
    
    def _generate_cache_key(
        self,
        message: str,
        client_type: str,
        context_hash: str = ""
    ) -> str:
        """
        Генерация уникального ключа кэша.
        Учитывает сообщение, тип клиента и контекст диалога.
        """
        # Нормализуем сообщение (убираем лишние пробелы, приводим к нижнему регистру)
        normalized_message = " ".join(message.lower().split())
        
        # Создаем хэш от сообщения
        message_hash = hashlib.md5(normalized_message.encode()).hexdigest()[:16]
        
        # Формируем ключ: cache:{client_type}:{message_hash}:{context_hash}
        key_parts = ["cache", client_type, message_hash]
        if context_hash:
            key_parts.append(context_hash[:8])
        
        return ":".join(key_parts)
    
    def _hash_context(self, conversation_history: list) -> str:
        """
        Хэшируем контекст диалога для учета истории.
        Если история меняется — кэш не используется.
        """
        if not conversation_history:
            return ""
        
        # Берем только последние 3 сообщения для контекста
        recent_history = conversation_history[-3:]
        context_str = json.dumps(recent_history, sort_keys=True)
        return hashlib.md5(context_str.encode()).hexdigest()
    
    async def get(
        self,
        message: str,
        client_type: str,
        conversation_history: list = None
    ) -> Optional[str]:
        """
        Получить кэшированный ответ.
        Возвращает None, если кэш не найден (cache miss).
        """
        try:
            context_hash = self._hash_context(conversation_history or [])
            cache_key = self._generate_cache_key(message, client_type, context_hash)
            
            cached_response = await self.redis.get(cache_key)
            
            if cached_response:
                print(f"INFO: Cache HIT cache_key={cache_key}", flush=True)
                logger.info(
                    "Cache HIT",
                    cache_key=cache_key,
                    message=message[:50]
                )
                # Увеличиваем счетчик использований (для статистики)
                await self.redis.incr(f"{cache_key}:hits")
                return cached_response if isinstance(cached_response, str) else cached_response.decode('utf-8')
            
            print(f"INFO: Cache MISS cache_key={cache_key}", flush=True)
            logger.info(
                "Cache MISS",
                cache_key=cache_key,
                message=message[:50]
            )
            return None
        
        except Exception as e:
            logger.error("Cache get error", error=str(e))
            return None  # При ошибке кэша — продолжаем без него
    
    async def set(
        self,
        message: str,
        client_type: str,
        response: str,
        conversation_history: list = None,
        ttl: int = None
    ) -> bool:
        """
        Сохранить ответ в кэш.
        """
        try:
            context_hash = self._hash_context(conversation_history or [])
            cache_key = self._generate_cache_key(message, client_type, context_hash)
            
            # Устанавливаем TTL (время жизни кэша)
            cache_ttl = ttl or self.default_ttl
            
            await self.redis.setex(
                cache_key,
                cache_ttl,
                response
            )
            
            # Инициализируем счетчик использований
            await self.redis.set(f"{cache_key}:hits", 0, ex=cache_ttl)
            
            print(f"INFO: Cache SET cache_key={cache_key} ttl={cache_ttl}", flush=True)
            logger.info(
                "Cache SET",
                cache_key=cache_key,
                ttl=cache_ttl,
                response_length=len(response)
            )
            return True
        
        except Exception as e:
            logger.error("Cache set error", error=str(e))
            return False
    
    async def invalidate(
        self,
        message: str,
        client_type: str,
        conversation_history: list = None
    ) -> bool:
        """
        Удалить конкретный кэш (например, при обновлении базы знаний).
        """
        try:
            context_hash = self._hash_context(conversation_history or [])
            cache_key = self._generate_cache_key(message, client_type, context_hash)
            
            await self.redis.delete(cache_key, f"{cache_key}:hits")
            
            logger.info("Cache invalidated", cache_key=cache_key)
            return True
        
        except Exception as e:
            logger.error("Cache invalidate error", error=str(e))
            return False
    
    async def clear_all(self) -> bool:
        """
        Очистить весь кэш (для админ-панели).
        """
        try:
            # Находим все ключи с префиксом "cache:"
            cursor = 0
            deleted_count = 0
            
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match="cache:*",
                    count=100
                )
                
                if keys:
                    await self.redis.delete(*keys)
                    deleted_count += len(keys)
                
                if cursor == 0:
                    break
            
            logger.info("All cache cleared", deleted_keys=deleted_count)
            return True
        
        except Exception as e:
            logger.error("Cache clear error", error=str(e))
            return False
    
    async def get_stats(self) -> dict:
        """
        Получить статистику кэша (для админ-панели).
        """
        try:
            # Считаем количество кэшированных ответов
            cursor = 0
            cache_keys = []
            
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match="cache:*",
                    count=100
                )
                
                # Фильтруем только основные ключи (без :hits)
                cache_keys.extend([k for k in keys if not k.endswith(':hits')])
                
                if cursor == 0:
                    break
            
            # Считаем общее количество использований
            total_hits = 0
            for key in cache_keys:
                hits = await self.redis.get(f"{key}:hits")
                if hits:
                    total_hits += int(hits)
            
            return {
                "cached_responses": len(cache_keys),
                "total_hits": total_hits,
                "avg_hits_per_cache": total_hits / len(cache_keys) if cache_keys else 0
            }
        
        except Exception as e:
            logger.error("Cache stats error", error=str(e))
            return {
                "cached_responses": 0,
                "total_hits": 0,
                "avg_hits_per_cache": 0
            }


# Функция для создания экземпляра (используется в dependencies.py)
def get_cache_service(redis_client: Redis) -> CacheService:
    """Dependency для получения CacheService."""
    return CacheService(redis_client)
    