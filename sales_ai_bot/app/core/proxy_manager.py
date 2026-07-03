# Proxy API management
import httpx
import random
from typing import Optional, List
from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()

class ProxyManager:
    """
    Менеджер прокси-серверов для ротации IP и безопасности запросов.
    Использует ProxyAPI для получения списка доступных прокси.
    """
    
    def __init__(self):
        self._proxy_pool: List[str] = []
        self._current_index = 0
    
    async def initialize(self) -> None:
        """
        Инициализация пула прокси.
        В MVP используем статический список. В продакшене — запрос к ProxyAPI.
        """
        if settings.DEBUG or not settings.PROXY_API_KEY or "your_proxy_key_here" in settings.PROXY_API_KEY:
            logger.info("Proxy pool initialization bypassed (direct connection enabled in debug/development)")
            self._proxy_pool = []
            return
            
        # Для MVP: статический список прокси
        # В реальности здесь будет запрос к ProxyAPI:
        # response = await httpx.get("https://proxyapi.example.com/get_proxies")
        self._proxy_pool = [
            "http://proxy1.example.com:8080",
            "http://proxy2.example.com:8080",
            "http://proxy3.example.com:8080",
        ]
        logger.info("Proxy pool initialized", pool_size=len(self._proxy_pool))
    
    def get_proxy(self) -> Optional[str]:
        """
        Получить следующий прокси по схеме Round-Robin.
        Если пул пуст — возвращаем None (прямое подключение).
        """
        if not self._proxy_pool:
            return None
        
        proxy = self._proxy_pool[self._current_index % len(self._proxy_pool)]
        self._current_index += 1
        return proxy
    
    def get_random_proxy(self) -> Optional[str]:
        """Получить случайный прокси из пула (для равномерной нагрузки)."""
        if not self._proxy_pool:
            return None
        return random.choice(self._proxy_pool)

# Глобальный экземпляр (синглтон)
proxy_manager = ProxyManager()
