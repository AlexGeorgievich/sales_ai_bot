# Sales AI Bot 🚀

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/features/actions)

Интеллектуальный чат-бот для автоматизации коммуникаций отдела продаж IT-компании. Бот интегрирован с большой языковой моделью **GigaChat** для обработки естественного языка и ответов на вопросы клиентов в дружелюбном и профессиональном стиле.

---

## 🎯 Решаемые проблемы (Бизнес-ценность)

* **Снижение нагрузки на отдел продаж:** Автоматические квалифицированные ответы на типовые вопросы (цены, стек технологий, этапы работы, гарантии) в режиме 24/7.
* **Адаптивный тон общения:** Бот настраивает стиль ответов под целевую аудиторию: дружелюбный с эмодзи для МСБ (малый и средний бизнес) и строгий/деловой для Enterprise-сегмента.
* **Удержание контекста:** Бот помнит историю диалога для более точных и релевантных ответов.
* **Повышение конверсии:** Мгновенные ответы на вопросы клиентов снижают процент отказов. При сложных запросах бот перенаправляет диалог на человека.
* **Аналитика взаимодействий:** Полный сбор и хранение данных о переписках для последующего улучшения скриптов продаж.

---

## ⚙️ Архитектурные и Технические решения

Для стабильности и отказоустойчивости системы под высокой нагрузкой внедрены следующие паттерны:

### 1. Circuit Breaker (Предохранитель)
Защищает приложение от каскадных сбоев при нестабильности GigaChat API. Если API начинает возвращать ошибки, предохранитель временно переходит в состояние `OPEN` и мгновенно возвращает вежливый fallback-ответ («*Извините, сейчас я не могу обработать ваш запрос...*»), не перегружая внешнюю сеть.

### 2. Умное Кэширование с Redis
Позволяет сократить время отклика бота до **< 0.01 сек** для повторных вопросов. 
* **Учет контекста:** Кэш-ключ генерируется на основе нормализованного вопроса, сегмента клиента и хэша последних 3-х сообщений истории диалога.
* **Персистентность (Persistence):** В `docker-compose.yml` включен режим **AOF (Append Only File)** для гарантированного сохранения кэша на диске при перезапуске контейнеров.

### 3. Обратный прокси-сервер Nginx
Маршрутизирует все запросы через единую точку входа (порт `80`):
* `/` — раздача статического контента лендинга.
* `/api/` — проксирование запросов к бэкенду FastAPI.
* `/api/docs` — проксирование Swagger UI (благодаря интеграции параметра `root_path="/api"` в FastAPI).

---

## 🛠️ Технологический стек

* **Бэкенд:** Python 3.11 / FastAPI / Uvicorn
* **СУБД:** PostgreSQL (SQLAlchemy + asyncpg для полностью асинхронного взаимодействия)
* **Кэширование:** Redis (асинхронный клиент `redis.asyncio`)
* **Интеграция с ИИ:** Официальный GigaChat SDK
* **Фронтенд:** HTML5 / CSS3 / Vanilla JS (интерактивный виджет чата)
* **Тестирование:** pytest / pytest-asyncio / pytest-cov (покрытие > 70%)
* **Окружение:** Docker / Docker Compose / Nginx
* **CI/CD:** GitHub Actions

---

## 🚀 Быстрый запуск

### Требования
* Установленный Docker и Docker Compose
* Ключ API GigaChat

### Шаги для запуска локально

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/AlexGeorgievich/sales_ai_bot.git
   cd sales_ai_bot
   ```

2. Создайте файл конфигурации `.env` на основе примера:
   ```bash
   cp .env.example .env
   ```
   *Заполните переменную `GIGACHAT_API_KEY` вашим ключом доступа.*

3. Запустите проект в Docker:
   ```bash
   docker-compose up --build
   ```

После сборки и запуска проект будет доступен по следующим адресам:
* 🌐 **Лендинг с виджетом:** [http://localhost](http://localhost)
* 📖 **Swagger API документация:** [http://localhost/api/docs](http://localhost/api/docs)

---

## 🧪 Тестирование

Для тестирования используется изолированная база данных **SQLite (in-memory)** и библиотека **fakeredis** (имитация Redis в памяти), что позволяет запускать тесты без поднятия реальной инфраструктуры.

### Запуск тестов локально

1. Активируйте виртуальное окружение:
   ```bash
   # Windows PowerShell
   . .\venv\Scripts\Activate.ps1
   ```
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Запустите тесты:
   ```bash
   # Обычный запуск
   python -m pytest -v

   # Запуск с отчетом о покрытии кода
   python -m pytest --cov=app --cov-report=term-missing
   ```

---

## 📡 API Эндпоинты

Основные эндпоинты бэкенда (доступны через Swagger на `/api/docs`):

| Метод | Путь | Описание |
| :--- | :--- | :--- |
| **POST** | `/chat/message` | Отправить сообщение боту (с поддержкой контекста и квалификации) |
| **GET** | `/chat/history/{session_id}` | Получить полную историю диалога сессии |
| **GET** | `/health` | Базовая проверка работоспособности сервиса |
| **GET** | `/health/cache-stats` | Получение статистики кэша Redis (hits/misses) |
| **POST** | `/health/cache-clear` | Полная очистка кэша Redis |
