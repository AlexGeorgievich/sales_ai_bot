# Инструкция по тестированию проекта Sales AI Bot 🧪

В проекте реализовано два уровня тестирования: бэкенд-тесты (юнит/интеграционные с эмуляцией БД и Redis) и фронтенд-тесты (сквозное E2E тестирование интерфейса лендинга и форм на Playwright).

---

## 1. Бэкенд-тестирование (Pytest)

Бэкенд-тесты проверяют API, кэширование и паттерн Circuit Breaker. Используется изолированная СУБД SQLite (in-memory) и `fakeredis`, поэтому запускать инфраструктуру в Docker не требуется.

### Запуск бэкенд-тестов:
1. Активируйте виртуальное окружение:
   ```bash
   # Windows PowerShell
   . .\venv\Scripts\Activate.ps1
   ```
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt -r requirements-admin.txt
   ```
3. Запустите тесты:
   ```bash
   python -m pytest tests/ -v --ignore=tests/test_frontend.py
   ```
4. Запуск с отчетом о покрытии кода (coverage):
   ```bash
   python -m pytest --cov=app --cov-report=term-missing --ignore=tests/test_frontend.py
   ```

---

## 2. Фронтенд-тестирование (Playwright)

Фронтенд-тесты проверяют корректность загрузки лендинга, переключение вкладок форм (B2B/B2C), работу маски телефонного ввода и отправку лидов (с перехватом и валидацией JSON-payload).

### Требования для запуска:
* Установленный Chromium браузер от Playwright.
* Запущенное локально веб-приложение (по умолчанию тесты обращаются к `http://localhost`).

### Запуск фронтенд-тестов:

1. Убедитесь, что контейнеры запущены:
   ```bash
   docker-compose up --build -d
   ```
2. Установите браузер Playwright (если еще не установлен):
   ```bash
   python -m playwright install chromium
   ```
3. Запустите тесты:
   ```bash
   python -m pytest tests/test_frontend.py -v
   ```

Для изменения базового URL тестируемого сайта используйте переменную окружения `PLAYWRIGHT_BASE_URL`:
```bash
$env:PLAYWRIGHT_BASE_URL="http://your-staging-url.com"
python -m pytest tests/test_frontend.py -v
```
