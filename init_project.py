import os
from pathlib import Path

def create_structure(base_path: str = "sales_ai_bot"):
    base = Path(base_path)
    
    # Список директорий
    dirs = [
        "app/api/v1",
        "app/core",
        "app/db",
        "app/schemas",
        "app/utils",
        "tests"
    ]
    
    # Список файлов с базовым содержимым
    files = {
        "app/__init__.py": "",
        "app/main.py": "# Main application entry point\n",
        "app/config.py": "# Configuration settings\n",
        "app/dependencies.py": "# Dependency injection\n",
        "app/api/__init__.py": "",
        "app/api/v1/__init__.py": "",
        "app/api/v1/chat.py": "# Chat endpoints\n",
        "app/api/v1/health.py": "# Health check endpoints\n",
        "app/core/__init__.py": "",
        "app/core/gigachat_service.py": "# GigaChat integration logic\n",
        "app/core/proxy_manager.py": "# Proxy API management\n",
        "app/core/security.py": "# Security utilities\n",
        "app/db/__init__.py": "",
        "app/db/session.py": "# Database session setup\n",
        "app/db/models.py": "# SQLAlchemy models\n",
        "app/db/repository.py": "# Data access layer\n",
        "app/schemas/__init__.py": "",
        "app/schemas/chat_schemas.py": "# Pydantic schemas for chat\n",
        "app/schemas/user_schemas.py": "# Pydantic schemas for users\n",
        "app/utils/__init__.py": "",
        "app/utils/logger.py": "# Logging configuration\n",
        "app/utils/prompts.py": "# System prompts\n",
        "tests/__init__.py": "",
        "tests/test_chat.py": "# Chat tests\n",
        ".env": "GIGACHAT_API_KEY=\nPROXY_API_KEY=\nDATABASE_URL=\n",
        ".gitignore": "__pycache__/\n.env\nvenv/\n*.pyc\n",
        "requirements.txt": "fastapi\nuvicorn\nsqlalchemy\nredis\nhttpx\ngigachat-python-sdk\nstructlog\npydantic-settings\n",
        "Dockerfile": "# Docker configuration will be added here\n",
        "README.md": "# Sales AI Bot MVP\n"
    }

    # Создаем директории
    for d in dirs:
        (base / d).mkdir(parents=True, exist_ok=True)
        
    # Создаем файлы
    for f, content in files.items():
        file_path = base / f
        if not file_path.exists():
            with open(file_path, 'w') as fp:
                fp.write(content)
                
    print(f"✅ Структура проекта успешно создана в папке '{base_path}'!")

if __name__ == "__main__":
    create_structure()