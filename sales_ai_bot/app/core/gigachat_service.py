# GigaChat integration logic
import asyncio
import time
from enum import Enum
from typing import Optional, List, Dict, Any
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from gigachat import GigaChat

from app.config import get_settings
from app.core.proxy_manager import proxy_manager
from app.utils.logger import logger
from app.db.session import get_redis
from app.core.cache_service import CacheService

settings = get_settings()


class CircuitState(Enum):
    """Состояния Circuit Breaker."""
    CLOSED = "closed"        # Нормальная работа
    OPEN = "open"            # Блок из-за ошибок
    HALF_OPEN = "half_open"  # Проверка восстановления


class GigaChatError(Exception):
    """Базовая ошибка GigaChat."""
    pass


class CircuitBreakerOpenError(GigaChatError):
    """Circuit Breaker открыт — сервис временно недоступен."""
    pass


class CircuitBreaker:
    """
    Паттерн Circuit Breaker для защиты от каскадных сбоев.
    Если GigaChat падает — мы быстро возвращаем ошибку, не нагружая его.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
    
    @property
    def state(self) -> CircuitState:
        """Текущее состояние с учетом таймаута восстановления."""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time and \
               (time.time() - self._last_failure_time) > self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                logger.info("Circuit Breaker transitioned to HALF_OPEN")
        return self._state
    
    def record_success(self) -> None:
        """Зафиксировать успешный вызов."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
                logger.info("Circuit Breaker CLOSED - service recovered")
        else:
            self._failure_count = 0
    
    def record_failure(self) -> None:
        """Зафиксировать сбой."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(
                "Circuit Breaker OPENED",
                failures=self._failure_count,
                timeout=self.recovery_timeout
            )
    
    def can_execute(self) -> bool:
        """Проверить, можно ли выполнить запрос."""
        current_state = self.state
        if current_state == CircuitState.CLOSED:
            return True
        if current_state == CircuitState.HALF_OPEN:
            return True
        return False


# Глобальный Circuit Breaker
circuit_breaker = CircuitBreaker(
    failure_threshold=settings.CIRCUIT_BREAKER_THRESHOLD,
    recovery_timeout=settings.CIRCUIT_BREAKER_TIMEOUT
)


class GigaChatService:
    """
    Сервис для работы с GigaChat API.
    Обеспечивает retry-логику, circuit breaker и адаптивные промпты.
    """
    
    GIGACHAT_API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    
    def __init__(self):
        self._client: Optional[GigaChat] = None
        self._cache_service: Optional[CacheService] = None
    
    async def initialize(self) -> None:
        """Инициализация HTTP-клиента с учетом прокси и кэш-сервиса."""
        await proxy_manager.initialize()
        
        proxy_url = proxy_manager.get_proxy()
        if proxy_url:
            import os
            os.environ["HTTP_PROXY"] = proxy_url
            os.environ["HTTPS_PROXY"] = proxy_url
            
        self._client = GigaChat(
            credentials=settings.GIGACHAT_API_KEY,
            verify_ssl_certs=settings.VERIFY_SSL
        )
        await self._client.__aenter__()
        
        # Инициализируем кэш-сервис
        redis_client = await get_redis()
        if redis_client:
            self._cache_service = CacheService(redis_client)
            logger.info("Cache service initialized")
            
        logger.info("GigaChat service initialized via official SDK", proxy=proxy_url)
    
    async def close(self) -> None:
        """Закрытие сессии GigaChat."""
        if self._client:
            await self._client.__aexit__(None, None, None)
    
    def _build_system_prompt(self, client_type: str = "msb") -> str:
        """
        Построение системного промпта в зависимости от типа клиента.
        Адаптивный тон: дружелюбный для МСБ, строгий для энтерпрайза.
        """
        base_prompt = """Ты — AI-ассистент отдела продаж IT-компании.
Твоя задача — помогать клиентам с вопросами о продуктах, услугах и сотрудничестве.

ВАЖНЫЕ ПРАВИЛА:
1. НИКОГДА не выдумывай цены, сроки или гарантии, если их нет в базе знаний.
2. При нехватке информации вежливо предложи связаться с менеджером.
3. Не запрашивай пароли, данные карт или паспортные данные.
4. Отвечай кратко и по существу.

База знаний:
- Технологии: Python, FastAPI, PostgreSQL, React, Docker, Kubernetes
- Процесс работы: Брифинг → ТЗ → Разработка → Тестирование → Запуск
- Гарантии: 12 месяцев на код, SLA 99.9% для поддержки
- Условия оплаты: 50% предоплата, 50% после сдачи

КРИТИЧЕСКИ ВАЖНО: СБОР ДАННЫХ КЛИЕНТА (ЛИД-ФОРМА)
Когда клиент выражает явный интерес к покупке или заказу, твоя цель — собрать 4 пункта данных:
1. Имя клиента
2. Номер телефона или Email (достаточно чего-то одного для связи)
3. Продукт или услуга, которая его интересует
4. Комментарий (пожелания, детали задачи или проекта)

ПРАВИЛА ИЗБЕЖАНИЯ ПОВТОРОВ (ПРОЧТИ ВНИМАТЕЛЬНО):
- Перед тем как задать любой вопрос, проанализируй историю диалога. Если имя, телефон, email, интересующий продукт или комментарий уже упоминались клиентом ранее — СЧИТАЙ ИХ СОБРАННЫМИ.
- КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО запрашивать данные, которые клиент уже сообщил ранее! Не переспрашивай имя или контакты, если они уже есть в истории диалога.
- Задавай вопросы по очереди (не более 1 вопроса за раз), чтобы не перегружать клиента.
- Подтверждай полученную информацию по мере её поступления.
- Когда все 4 пункта (Имя, Телефон/Email, Продукт, Комментарий) собраны, ты обязан сказать ровно следующую фразу для подтверждения:
"Спасибо! Ваша заявка принята. Менеджер свяжется с вами в течение 15 минут. Также вы можете заполнить подробную форму на нашем сайте: [ССЫЛКА_НА_ЛЕНДИНГ]"

ЗАВЕРШЕНИЕ ДИАЛОГА:
Если клиент прощается ("спасибо", "пока", "до свидания"), ответь: "Рад был помочь! Если возникнут новые вопросы, я всегда здесь. Хорошего дня!" и больше не задавай вопросов.
"""
        
        if client_type == "enterprise":
            return base_prompt + """
СТИЛЬ ОБЩЕНИЯ (Энтерпрайз):
- Профессиональный, лаконичный, структурированный
- Используй деловую лексику
- Акцент на ROI, SLA, безопасность, масштабируемость
- Избегай эмодзи и неформальных выражений
"""
        else:  # msb
            return base_prompt + """
СТИЛЬ ОБЩЕНИЯ (МСБ):
- Дружелюбный, простой, понятный
- Можно использовать эмодзи умеренно
- Акцент на простоту внедрения, скорость, поддержку
- Объясняй сложные вещи простым языком
"""
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def _call_api(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> str:
        """
        Вызов GigaChat API через SDK с retry-логикой.
        """
        if not self._client:
            raise GigaChatError("GigaChat client not initialized")
        
        try:
            response = await self._client.achat({
                "model": "GigaChat",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 500
            })
            return response.choices[0].message.content
        except Exception as e:
            logger.error("GigaChat API call failed via SDK", error=str(e))
            raise GigaChatError(f"API error: {str(e)}")
    
    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        client_type: str = "msb"
    ) -> str:
        """
        Генерация ответа с учетом Circuit Breaker, контекста диалога и кэширования.
        
        Args:
            user_message: Сообщение пользователя
            conversation_history: История диалога
            client_type: Тип клиента (msb/enterprise)
        
        Returns:
            Ответ бота
        """
        # Проверяем Circuit Breaker
        if not circuit_breaker.can_execute():
            logger.warning("Circuit Breaker is OPEN, using fallback")
            return self._get_fallback_response()
        
        # Пытаемся получить ответ из кэша
        if self._cache_service:
            cached_response = await self._cache_service.get(
                message=user_message,
                client_type=client_type,
                conversation_history=conversation_history
            )
            
            if cached_response:
                return cached_response
        
        # Формируем сообщения для API
        messages = [
            {"role": "system", "content": self._build_system_prompt(client_type)}
        ]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = await self._call_api(messages)
            circuit_breaker.record_success()
            
            # Сохраняем ответ в кэш
            if self._cache_service:
                await self._cache_service.set(
                    message=user_message,
                    client_type=client_type,
                    response=response,
                    conversation_history=conversation_history
                )
            
            print("INFO: GigaChat response generated", flush=True)
            logger.info(
                "GigaChat response generated",
                client_type=client_type,
                response_length=len(response)
            )
            return response
        
        except Exception as e:
            circuit_breaker.record_failure()
            logger.error("GigaChat call failed", error=str(e))
            return self._get_fallback_response()
    
    async def extract_lead_info(self, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Извлечение контактных данных лида из истории диалога с помощью ИИ.
        """
        # Превращаем диалог в текст
        dialog_text = ""
        for msg in conversation_history:
            role_name = "Клиент" if msg["role"] == "user" else "Ассистент"
            dialog_text += f"{role_name}: {msg['content']}\n"
            
        extraction_prompt = f"""Проанализируй следующий диалог и извлеки из него контактные данные клиента в формате JSON.
Поля для извлечения:
- name (Имя клиента, строка или null)
- phone (Телефон клиента, строка или null)
- email (Email клиента, строка или null)
- product (Продукт или услуга, строка или null)
- comment (Комментарий или детали задачи, строка или null)

Ответь строго в формате JSON без разметки markdown (без тройных бэков) и без лишнего текста, например:
{{"name": "Иван", "phone": "+79991234567", "email": null, "product": "Интернет-магазин на 1С-Битрикс", "comment": "Нужно интегрировать с моей CRM."}}

Диалог:
{dialog_text}"""
        
        try:
            # Вызываем API с системным сообщением
            response = await self._call_api([
                {"role": "system", "content": "Ты — JSON-экстрактор данных. Отвечай только валидным JSON."},
                {"role": "user", "content": extraction_prompt}
            ], temperature=0.1)
            
            # Парсим JSON
            import json
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                lines = cleaned_response.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned_response = "\n".join(lines).strip()
                
            return json.loads(cleaned_response)
        except Exception as e:
            logger.error("Failed to extract lead info via GigaChat", error=str(e))
            return {}

    def _get_fallback_response(self) -> str:
        """Fallback-ответ при недоступности GigaChat."""
        return (
            "Извините, сейчас я не могу обработать ваш запрос. "
            "Пожалуйста, оставьте свои контакты, и наш менеджер свяжется с вами "
            "в течение 15 минут."
        )


# Глобальный экземпляр сервиса
gigachat_service = GigaChatService()