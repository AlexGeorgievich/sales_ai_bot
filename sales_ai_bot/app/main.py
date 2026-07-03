from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.config import get_settings
from app.utils.logger import logger
from app.api.v1.health import router as health_router
from app.api.v1.chat import router as chat_router
from app.core.gigachat_service import gigachat_service
from app.db.session import init_db, close_db

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    # Startup
    logger.info(
        "Starting application",
        project=settings.PROJECT_NAME,
        version=settings.VERSION
    )
    
    # Инициализируем БД
    await init_db()
    logger.info("Database initialized")
    
    # Инициализируем GigaChat сервис
    await gigachat_service.initialize()
    logger.info("GigaChat service initialized")
    
    yield
    
    # Shutdown
    await gigachat_service.close()
    await close_db()
    logger.info("Application shutdown complete")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    root_path="/api",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)

# Раздача статики для виджета
app.mount("/widget", StaticFiles(directory="widget"), name="widget")

@app.get("/")
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running"
    }
