import pytest
import pytest_asyncio
import allure
import os
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock
from fakeredis.aioredis import FakeRedis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.db.session import get_db_session, get_redis
from app.core.cache_service import CacheService
from app.core.gigachat_service import GigaChatService


# Тестовая база данных (SQLite в памяти для скорости)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """
    Фикстура для тестовой сессии БД.
    Создает таблицы перед тестом и удаляет после.
    """
    from app.db.session import Base
    
    # Создаем таблицы
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Создаем сессию
    async with TestSessionLocal() as session:
        yield session
    
    # Удаляем таблицы
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def fake_redis():
    """
    Фикстура для фейкового Redis (fakeredis).
    Работает в памяти, не требует реального Redis.
    """
    redis = FakeRedis(decode_responses=True)
    yield redis
    await redis.flushall()
    await redis.close()


@pytest_asyncio.fixture(scope="function")
async def cache_service(fake_redis):
    """Фикстура для CacheService с фейковым Redis."""
    return CacheService(fake_redis)


@pytest_asyncio.fixture(scope="function")
async def client(db_session, fake_redis):
    """
    Фикстура для тестового HTTP-клиента.
    Переопределяет зависимости на тестовые версии.
    """
    
    async def override_get_db():
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def override_get_redis():
        return fake_redis
    
    # Переопределяем зависимости
    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    
    # Создаем тестовый клиент
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client
    
    # Очищаем overrides
    app.dependency_overrides.clear()


@pytest.fixture
def mock_gigachat_response():
    """Фикстура с примером ответа от GigaChat."""
    return "Стоимость разработки сайта зависит от сложности проекта. Для точной оценки свяжитесь с нашим менеджером."


@pytest_asyncio.fixture
async def gigachat_service_mock(mock_gigachat_response):
    """
    Фикстура для мока GigaChatService.
    Вместо реальных запросов возвращает заглушку.
    """
    service = GigaChatService()
    service._cache_service = None  # Отключаем кэш для изоляции тестов
    
    # Мокаем метод _call_api
    service._call_api = AsyncMock(return_value=mock_gigachat_response)
    
    return service


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Данный хук позволяет узнать результат выполнения теста."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(scope="function")
def page(context, request):
    """
    Переопределенная фикстура page из pytest-playwright.
    Автоматически закрывает контекст по завершению теста,
    после чего прикрепляет записанное видео и скриншот финала/ошибки в Allure.
    """
    p = context.new_page()
    yield p
    
    # Снимаем скриншот финального состояния страницы
    try:
        screenshot_bytes = p.screenshot(full_page=True)
        allure.attach(
            screenshot_bytes,
            name="final_screenshot",
            attachment_type=allure.attachment_type.PNG
        )
    except Exception:
        pass

    # Закрываем контекст, чтобы Playwright сохранил видео на диск
    context.close()
    
    # Находим видео и прикрепляем к Allure
    video = p.video
    if video:
        try:
            video_path = video.path()
            if video_path and os.path.exists(video_path):
                allure.attach.file(
                    video_path,
                    name="video_walkthrough",
                    attachment_type=allure.attachment_type.WEBM
                )
        except Exception:
            pass


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """
    Устанавливает дефолтный размер экрана для всех тестов (1280x720).
    Предотвращает появление серых полей по бокам видеозаписи.
    """
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
    }


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """
    Добавляет аргументы запуска для Chromium.
    Отключение GPU предотвращает баги рендеринга и серые засветки экрана в headless-режиме на Windows.
    """
    return {
        **browser_type_launch_args,
        "args": [
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--window-size=1280,720",
        ],
    }


@pytest.fixture(autouse=True)
def set_allure_title_from_docstring(request):
    """
    Автоматически устанавливает заголовок теста в Allure-отчете
    на основе первой строки его docstring.
    """
    try:
        if request.node and hasattr(request.node, "obj") and request.node.obj:
            doc = request.node.obj.__doc__
            if doc:
                first_line = doc.strip().split("\n")[0].strip()
                if first_line:
                    allure.dynamic.title(first_line)
    except Exception:
        pass
