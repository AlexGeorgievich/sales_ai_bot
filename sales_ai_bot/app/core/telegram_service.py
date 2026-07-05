import httpx
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)


class TelegramService:
    @staticmethod
    async def send_lead_notification(
        client_name: str,
        client_phone: str,
        client_email: str,
        interested_product: str,
        client_comment: str,
        client_type: str
    ) -> bool:
        """
        Отправляет форматированное HTML-сообщение о новом лиде в Telegram-чат/канал.
        """
        settings = get_settings()
        bot_token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID

        if not bot_token or not chat_id:
            logger.info("Telegram notification skipped: bot credentials not fully configured.")
            return False

        client_type_ru = "Крупный бизнес (B2B / Enterprise)" if client_type == "enterprise" else "Малый и средний бизнес (B2C / МСБ)"

        text = (
            f"🔔 <b>Новый лид в Sales AI Bot!</b>\n\n"
            f"👤 <b>Имя:</b> {client_name or 'Не указано'}\n"
            f"📞 <b>Телефон:</b> {client_phone or 'Не указан'}\n"
            f"📧 <b>Email:</b> {client_email or 'Не указан'}\n"
            f"🎯 <b>Продукт:</b> {interested_product or 'Не выбран'}\n"
            f"💬 <b>Комментарий:</b> {client_comment or 'Нет'}\n"
            f"🏷️ <b>Сегмент:</b> {client_type_ru}\n"
        )

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    logger.info("Telegram notification successfully sent.")
                    return True
                else:
                    logger.error(
                        f"Failed to send Telegram notification (status_code={response.status_code}): {response.text}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {str(e)}")
            return False
