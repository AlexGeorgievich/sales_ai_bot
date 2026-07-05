import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.telegram_service import TelegramService
from app.config import Settings


@pytest.mark.asyncio
async def test_telegram_skipped_when_not_configured():
    """Тест: отправка пропускается, если нет токена или чата."""
    mock_settings = Settings(TELEGRAM_BOT_TOKEN="", TELEGRAM_CHAT_ID="")
    
    with patch("app.core.telegram_service.get_settings", return_value=mock_settings):
        res = await TelegramService.send_lead_notification(
            client_name="Тест",
            client_phone="123",
            client_email="test@test.ru",
            interested_product="CRM",
            client_comment="Тестовый коммент",
            client_type="msb"
        )
        assert res is False


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_telegram_success_sends_notification(mock_post):
    """Тест: успешная отправка уведомления в Telegram."""
    mock_settings = Settings(
        TELEGRAM_BOT_TOKEN="mock_token",
        TELEGRAM_CHAT_ID="mock_chat"
    )
    
    # Имитируем успешный HTTP-ответ
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    with patch("app.core.telegram_service.get_settings", return_value=mock_settings):
        res = await TelegramService.send_lead_notification(
            client_name="Иван Иванов",
            client_phone="+79991112233",
            client_email="ivan@ivanov.ru",
            interested_product="Разработка сайтов",
            client_comment="Срочно",
            client_type="enterprise"
        )
        
        assert res is True
        mock_post.assert_called_once()
        
        # Проверяем, что в запросе передан верный payload
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.telegram.org/botmock_token/sendMessage"
        assert kwargs["json"]["chat_id"] == "mock_chat"
        assert "Иван Иванов" in kwargs["json"]["text"]
        assert "+79991112233" in kwargs["json"]["text"]
        assert "Крупный бизнес (B2B / Enterprise)" in kwargs["json"]["text"]


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_telegram_failed_response_returns_false(mock_post):
    """Тест: обработка сбоя ответа API Telegram."""
    mock_settings = Settings(
        TELEGRAM_BOT_TOKEN="mock_token",
        TELEGRAM_CHAT_ID="mock_chat"
    )
    
    # Имитируем ошибку (400 Bad Request)
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_post.return_value = mock_response
    
    with patch("app.core.telegram_service.get_settings", return_value=mock_settings):
        res = await TelegramService.send_lead_notification(
            client_name="Иван Иванов",
            client_phone="123",
            client_email="ivan@ivanov.ru",
            interested_product="Сайт",
            client_comment="",
            client_type="msb"
        )
        
        assert res is False
