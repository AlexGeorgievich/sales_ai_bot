from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sales AI Bot"
    VERSION: str = "0.1.0"
    MAX_CONCURRENT_SESSIONS: int = 10
    DEBUG: bool = True
    
    # Circuit Breaker & Timeout settings
    CIRCUIT_BREAKER_THRESHOLD: int = 5
    CIRCUIT_BREAKER_TIMEOUT: int = 60
    RESPONSE_TIMEOUT: int = 2
    
    # API Keys and URLs
    GIGACHAT_API_KEY: str = ""
    PROXY_API_KEY: str = ""
    DATABASE_URL: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    VERIFY_SSL: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
