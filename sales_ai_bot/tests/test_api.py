import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Тесты для health-check endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Health endpoint должен возвращать статус healthy."""
        response = await client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    @pytest.mark.asyncio
    async def test_readiness_check(self, client: AsyncClient):
        """Readiness endpoint должен возвращать статус ready."""
        response = await client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"


class TestChatEndpoints:
    """Тесты для chat endpoints."""
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, client: AsyncClient):
        """Должен успешно обрабатывать сообщение."""
        payload = {
            "user_id": "test_user_1",
            "message": "Привет",
            "client_type": "msb",
            "session_id": "test_session_1"
        }
        
        response = await client.post("/chat/message", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user_1"
        assert data["session_id"] == "test_session_1"
        assert "response" in data
        assert len(data["response"]) > 0
    
    @pytest.mark.asyncio
    async def test_send_message_validates_client_type(self, client: AsyncClient):
        """Должен валидировать тип клиента."""
        payload = {
            "user_id": "test_user_1",
            "message": "Привет",
            "client_type": "invalid_type"  # Невалидный тип
        }
        
        response = await client.post("/chat/message", json=payload)
        
        assert response.status_code == 422  # Validation Error
    
    @pytest.mark.asyncio
    async def test_send_message_validates_message_length(self, client: AsyncClient):
        """Должен валидировать длину сообщения."""
        payload = {
            "user_id": "test_user_1",
            "message": "",  # Пустое сообщение
            "client_type": "msb"
        }
        
        response = await client.post("/chat/message", json=payload)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_chat_history(self, client: AsyncClient):
        """Должен возвращать историю диалога."""
        # Сначала отправляем сообщение
        payload = {
            "user_id": "test_user_2",
            "message": "Тестовое сообщение",
            "client_type": "msb",
            "session_id": "test_session_2"
        }
        await client.post("/chat/message", json=payload)
        
        # Получаем историю
        response = await client.get("/chat/history/test_session_2")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    @pytest.mark.asyncio
    async def test_get_chat_history_not_found(self, client: AsyncClient):
        """Должен возвращать 404 для несуществующей сессии."""
        response = await client.get("/chat/history/nonexistent_session")
        
        assert response.status_code == 404


class TestCacheEndpoints:
    """Тесты для cache endpoints."""
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, client: AsyncClient):
        """Должен возвращать статистику кэша."""
        response = await client.get("/health/cache-stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["cache_enabled"] is True
        assert "stats" in data
    
    @pytest.mark.asyncio
    async def test_cache_clear(self, client: AsyncClient):
        """Должен очищать кэш."""
        response = await client.post("/health/cache-clear")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        