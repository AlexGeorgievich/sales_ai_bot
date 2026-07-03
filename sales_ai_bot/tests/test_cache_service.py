import pytest
from app.core.cache_service import CacheService


class TestCacheService:
    """Тесты для CacheService."""
    
    @pytest.mark.asyncio
    async def test_cache_miss_returns_none(self, cache_service):
        """Cache miss должен возвращать None."""
        result = await cache_service.get(
            message="Тестовый вопрос",
            client_type="msb"
        )
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, cache_service):
        """Должен сохранять и возвращать кэшированный ответ."""
        message = "Сколько стоит сайт?"
        client_type = "msb"
        response = "Стоимость от 100 000 рублей."
        
        # Сохраняем в кэш
        success = await cache_service.set(
            message=message,
            client_type=client_type,
            response=response
        )
        assert success is True
        
        # Получаем из кэша
        cached = await cache_service.get(
            message=message,
            client_type=client_type
        )
        assert cached == response
    
    @pytest.mark.asyncio
    async def test_cache_differentiates_by_client_type(self, cache_service):
        """Кэш должен различать ответы для разных типов клиентов."""
        message = "Сколько стоит сайт?"
        
        # Сохраняем для МСБ
        await cache_service.set(
            message=message,
            client_type="msb",
            response="Ответ для МСБ"
        )
        
        # Сохраняем для энтерпрайза
        await cache_service.set(
            message=message,
            client_type="enterprise",
            response="Ответ для энтерпрайза"
        )
        
        # Проверяем, что ответы разные
        msb_response = await cache_service.get(message, "msb")
        enterprise_response = await cache_service.get(message, "enterprise")
        
        assert msb_response == "Ответ для МСБ"
        assert enterprise_response == "Ответ для энтерпрайза"
    
    @pytest.mark.asyncio
    async def test_cache_considers_conversation_context(self, cache_service):
        """Кэш должен учитывать контекст диалога."""
        message = "Расскажи подробнее"
        
        # Контекст 1
        context1 = [
            {"role": "user", "content": "Сколько стоит сайт?"},
            {"role": "assistant", "content": "От 100 000 рублей."}
        ]
        
        # Контекст 2
        context2 = [
            {"role": "user", "content": "Какие гарантии?"},
            {"role": "assistant", "content": "12 месяцев."}
        ]
        
        # Сохраняем с разными контекстами
        await cache_service.set(
            message=message,
            client_type="msb",
            response="Ответ в контексте 1",
            conversation_history=context1
        )
        
        await cache_service.set(
            message=message,
            client_type="msb",
            response="Ответ в контексте 2",
            conversation_history=context2
        )
        
        # Проверяем, что ответы разные
        response1 = await cache_service.get(message, "msb", context1)
        response2 = await cache_service.get(message, "msb", context2)
        
        assert response1 == "Ответ в контексте 1"
        assert response2 == "Ответ в контексте 2"
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cache_service):
        """Должен удалять конкретный кэш."""
        message = "Тестовый вопрос"
        
        # Сохраняем в кэш
        await cache_service.set(
            message=message,
            client_type="msb",
            response="Ответ"
        )
        
        # Проверяем, что кэш есть
        cached = await cache_service.get(message, "msb")
        assert cached == "Ответ"
        
        # Инвалидируем кэш
        success = await cache_service.invalidate(message, "msb")
        assert success is True
        
        # Проверяем, что кэш удален
        cached = await cache_service.get(message, "msb")
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_cache_clear_all(self, cache_service):
        """Должен очищать весь кэш."""
        # Сохраняем несколько записей
        await cache_service.set("Вопрос 1", "msb", "Ответ 1")
        await cache_service.set("Вопрос 2", "msb", "Ответ 2")
        await cache_service.set("Вопрос 3", "enterprise", "Ответ 3")
        
        # Проверяем статистику
        stats = await cache_service.get_stats()
        assert stats["cached_responses"] == 3
        
        # Очищаем весь кэш
        success = await cache_service.clear_all()
        assert success is True
        
        # Проверяем, что кэш пуст
        stats = await cache_service.get_stats()
        assert stats["cached_responses"] == 0
    
    @pytest.mark.asyncio
    async def test_cache_tracks_hits(self, cache_service):
        """Должен отслеживать количество использований кэша."""
        message = "Популярный вопрос"
        
        # Сохраняем в кэш
        await cache_service.set(message, "msb", "Ответ")
        
        # Обращаемся к кэшу 5 раз
        for _ in range(5):
            await cache_service.get(message, "msb")
        
        # Проверяем статистику
        stats = await cache_service.get_stats()
        assert stats["cached_responses"] == 1
        assert stats["total_hits"] == 5
        