import pytest
import os
import uuid
from playwright.sync_api import Page, expect

# Базовый URL страницы лендинга и админ-панели
BASE_URL = os.getenv("PLAYWRIGHT_BASE_URL", "http://localhost")
ADMIN_URL = os.getenv("PLAYWRIGHT_ADMIN_URL", "http://localhost:8501")

# ==========================================
# 1. ТЕСТЫ ЗАГРУЗКИ, НАВИГАЦИИ И АДАПТИВНОСТИ
# ==========================================

def test_landing_page_load(page: Page):
    """Тест 1: Проверка базовой загрузки лендинга, логотипа и hero-секции."""
    page.goto(BASE_URL)
    expect(page).to_have_title("NexusCode — Разработка. Внедрение. Обучение.")
    expect(page.locator("nav.navbar")).to_be_visible()
    expect(page.locator("nav.navbar .logo-text")).to_have_text("NexusCode")
    expect(page.locator("section#hero")).to_be_visible()
    expect(page.locator("h1")).to_contain_text("Разработка. Внедрение.")

def test_landing_navigation_scroll(page: Page):
    """Тест 2: Проверка навигационных якорных ссылок на лендинге."""
    page.goto(BASE_URL)
    # Нажимаем на ссылку "Услуги" в шапке
    page.click("nav.navbar a[href='#services']")
    # Секция услуг должна находиться в зоне видимости
    expect(page.locator("section#services")).to_be_in_viewport()

def test_landing_mobile_hamburger_menu(page: Page):
    """Тест 3: Проверка мобильной адаптивности навигационного меню (бургер-меню)."""
    # Симулируем мобильный вьюпорт (iPhone 12 / 375x812)
    page.set_viewport_size({"width": 375, "height": 812})
    page.goto(BASE_URL)
    
    # Кнопка бургера должна быть видима, а ссылки меню скрыты
    burger = page.locator("button#burger")
    expect(burger).to_be_visible()
    
    # Кликаем по бургер-меню
    burger.click()
    # Навигационное меню должно открыться/стать видимым
    expect(page.locator("ul#navLinks")).to_be_visible()

# ==========================================
# 2. ТЕСТЫ ВКЛАДОК И ВАЛИДАЦИИ ФОРМ
# ==========================================

def test_form_tabs_switching(page: Page):
    """Тест 4: Переключение вкладок B2B и B2C форм."""
    page.goto(BASE_URL)
    
    # По умолчанию B2B активна, B2C скрыта
    expect(page.locator("#formB2B")).to_be_visible()
    expect(page.locator("#formB2C")).to_have_class(r"contact-form hidden")
    
    # Переключение на B2C
    page.click("button[data-tab='b2c']")
    expect(page.locator("#formB2C")).to_be_visible()
    expect(page.locator("#formB2B")).to_have_class(r"contact-form hidden")

def test_b2b_form_validation_required_fields(page: Page):
    """Тест 5: HTML5 валидация обязательного поля Имя в форме B2B."""
    page.goto(BASE_URL)
    # Очищаем имя и пытаемся отправить
    page.locator("#b2b-name").fill("")
    page.click("#formB2B button[type='submit']")
    
    # Проверяем, что форма не отправлена и поле имени имеет статус invalid
    is_valid = page.evaluate("document.getElementById('b2b-name').checkValidity()")
    assert is_valid is False

def test_b2b_form_validation_email(page: Page):
    """Тест 6: Валидация формата Email в форме B2B."""
    page.goto(BASE_URL)
    page.fill("#b2b-name", "Тест")
    page.fill("#b2b-company", "ТестКомпани")
    # Вводим некорректный email
    page.fill("#b2b-email", "invalid-email")
    page.click("#formB2B button[type='submit']")
    
    is_valid = page.evaluate("document.getElementById('b2b-email').checkValidity()")
    assert is_valid is False

def test_b2b_form_validation_privacy(page: Page):
    """Тест 7: Валидация обязательного согласия с политикой конфиденциальности (B2B)."""
    page.goto(BASE_URL)
    page.fill("#b2b-name", "Иван")
    page.fill("#b2b-company", "Тест")
    page.fill("#b2b-email", "test@test.ru")
    # Снимаем чекбокс согласия (он по умолчанию может быть не отмечен)
    page.uncheck("#formB2B input[name='privacy']")
    page.click("#formB2B button[type='submit']")
    
    is_valid = page.evaluate("document.querySelector('#formB2B input[name=\"privacy\"]').checkValidity()")
    assert is_valid is False

def test_b2b_phone_mask(page: Page):
    """Тест 8: Маска ввода телефона формы B2B (+7 (XXX) XXX-XX-XX)."""
    page.goto(BASE_URL)
    phone_input = page.locator("#b2b-phone")
    phone_input.fill("9991234567")
    expect(phone_input).to_have_value("+7 (999) 123-45-67")

def test_b2c_form_validation_required_fields(page: Page):
    """Тест 9: HTML5 валидация обязательного поля Имя в форме B2C."""
    page.goto(BASE_URL)
    page.click("button[data-tab='b2c']")
    page.locator("#b2c-name").fill("")
    page.click("#formB2C button[type='submit']")
    
    is_valid = page.evaluate("document.getElementById('b2c-name').checkValidity()")
    assert is_valid is False

def test_b2c_form_validation_email(page: Page):
    """Тест 10: Валидация формата Email в форме B2C."""
    page.goto(BASE_URL)
    page.click("button[data-tab='b2c']")
    page.fill("#b2c-name", "Алексей")
    page.fill("#b2c-email", "notanemail")
    page.click("#formB2C button[type='submit']")
    
    is_valid = page.evaluate("document.getElementById('b2c-email').checkValidity()")
    assert is_valid is False

def test_b2c_form_validation_privacy(page: Page):
    """Тест 11: Валидация согласия с политикой конфиденциальности (B2C)."""
    page.goto(BASE_URL)
    page.click("button[data-tab='b2c']")
    page.fill("#b2c-name", "Алексей")
    page.fill("#b2c-email", "b2c@test.ru")
    page.uncheck("#formB2C input[name='privacy']")
    page.click("#formB2C button[type='submit']")
    
    is_valid = page.evaluate("document.querySelector('#formB2C input[name=\"privacy\"]').checkValidity()")
    assert is_valid is False

def test_b2c_phone_mask(page: Page):
    """Тест 12: Маска ввода телефона формы B2C."""
    page.goto(BASE_URL)
    page.click("button[data-tab='b2c']")
    phone_input = page.locator("#b2c-phone")
    phone_input.fill("9001112233")
    expect(phone_input).to_have_value("+7 (900) 111-22-33")

# ==========================================
# 3. ТЕСТЫ ОТПРАВКИ И СТРУКТУРЫ PAYLOAD
# ==========================================

def test_b2b_submission_payload_with_mock(page: Page):
    """Тест 13: Проверка структуры отправляемого JSON-payload для формы B2B."""
    page.goto(BASE_URL)
    captured_payload = {}
    
    # Настраиваем перехват запроса к API сохранения лидов
    def handle_route(route):
        nonlocal captured_payload
        request = route.request
        if request.method == "POST" and "chat/leads" in request.url:
            captured_payload.update(request.post_data_json)
        route.fulfill(status=201, json={"status": "success", "id": 1})
        
    page.route("**/chat/leads", handle_route)
    
    # Заполнение
    page.fill("#b2b-name", "Иван Иванов")
    page.fill("#b2b-company", "ООО Ромашка")
    page.fill("#b2b-email", "romashka@b2b.ru")
    page.fill("#b2b-phone", "9555555555")
    page.select_option("#b2b-service", "implementation")
    page.fill("#b2b-message", "Требуется CRM")
    page.check("#formB2B input[name='privacy']")
    
    page.click("#formB2B button[type='submit']")
    
    # Успешный экран
    expect(page.locator("#formSuccess")).to_be_visible()
    
    # Валидация полей
    assert captured_payload["client_name"] == "Иван Иванов"
    assert captured_payload["client_email"] == "romashka@b2b.ru"
    assert captured_payload["client_phone"] == "+7 (955) 555-55-55"
    assert captured_payload["interested_product"] == "implementation"
    assert captured_payload["client_type"] == "enterprise"
    assert "ООО Ромашка" in captured_payload["client_comment"]

def test_b2c_submission_payload_with_mock(page: Page):
    """Тест 14: Проверка структуры отправляемого JSON-payload для формы B2C."""
    page.goto(BASE_URL)
    page.click("button[data-tab='b2c']")
    captured_payload = {}
    
    def handle_route(route):
        nonlocal captured_payload
        request = route.request
        if request.method == "POST" and "chat/leads" in request.url:
            captured_payload.update(request.post_data_json)
        route.fulfill(status=201, json={"status": "success", "id": 2})
        
    page.route("**/chat/leads", handle_route)
    
    page.fill("#b2c-name", "Анна Смирнова")
    page.fill("#b2c-email", "anna@example.com")
    page.fill("#b2c-phone", "9007778899")
    page.select_option("#b2c-interest", "ai-dev")
    page.fill("#b2c-message", "Интересует курс")
    page.check("#formB2C input[name='privacy']")
    
    page.click("#formB2C button[type='submit']")
    expect(page.locator("#formSuccess")).to_be_visible()
    
    assert captured_payload["client_name"] == "Анна Смирнова"
    assert captured_payload["client_email"] == "anna@example.com"
    assert captured_payload["client_phone"] == "+7 (900) 777-88-99"
    assert captured_payload["interested_product"] == "ai-dev"
    assert captured_payload["client_comment"] == "Интересует курс"
    assert captured_payload["client_type"] == "msb"

# ==========================================
# 4. ТЕСТЫ ЧАТ-БОТА (ИНТЕРАКТИВНЫЙ ВИДЖЕТ)
# ==========================================

def test_chat_widget_toggle_ui(page: Page):
    """Тест 15: Открытие и закрытие виджета чата."""
    page.goto(BASE_URL)
    
    toggle_btn = page.locator("#sales-ai-toggle")
    chat_container = page.locator("#sales-ai-chat")
    close_btn = page.locator("#sales-ai-close")
    
    expect(toggle_btn).to_be_visible()
    expect(chat_container).not_to_have_class("open")
    
    # Открываем чат
    toggle_btn.click()
    expect(chat_container).to_have_class(r"sales-ai-chat-container open")
    
    # Закрываем чат
    close_btn.click()
    expect(chat_container).not_to_have_class("open")

def test_chat_widget_welcome_message(page: Page):
    """Тест 16: Отображение приветственного сообщения при открытии чата."""
    page.goto(BASE_URL)
    page.click("#sales-ai-toggle")
    
    # Приветственное сообщение должно быть на экране
    welcome_bubble = page.locator("#sales-ai-messages .sales-ai-message.bot .sales-ai-message-bubble")
    expect(welcome_bubble).to_be_visible()
    expect(welcome_bubble).to_contain_text("Здравствуйте!")

def test_chat_widget_send_message_mock(page: Page):
    """Тест 17: Имитация отправки сообщения и получения ответа от ИИ."""
    page.goto(BASE_URL)
    page.click("#sales-ai-toggle")
    
    # Перехватываем запрос к боту
    page.route("**/chat/message", lambda route: route.fulfill(
        status=200, 
        json={"response": "Я могу помочь с интеграцией GigaChat API."}
    ))
    
    page.fill("#sales-ai-input", "Расскажи про GigaChat")
    page.press("#sales-ai-input", "Enter")
    
    # Проверяем, что сообщение пользователя появилось в чате
    expect(page.locator("#sales-ai-messages .sales-ai-message.user .sales-ai-message-bubble")).to_contain_text("Расскажи про GigaChat")
    
    # Ожидаем появление ответа бота
    bot_messages = page.locator("#sales-ai-messages .sales-ai-message.bot .sales-ai-message-bubble")
    # Должно быть 2 сообщения от бота: приветствие и ответ на вопрос
    expect(bot_messages).to_have_count(2)
    expect(bot_messages.nth(1)).to_have_text("Я могу помочь с интеграцией GigaChat API.")

# ==========================================
# 5. ИНТЕГРАЦИОННЫЕ E2E СЦЕНАРИИ
# ==========================================

def test_e2e_integration_b2b_form_to_streamlit_admin(page: Page):
    """
    Тест 18: Полный E2E-сценарий (B2B).
    Регистрация лида на лендинге -> Проверка его появления в админ-панели Streamlit.
    """
    # 1. Генерируем уникальное имя для лида, чтобы избежать пересечений
    unique_id = str(uuid.uuid4())[:8]
    lead_name = f"E2E_B2B_Lead_{unique_id}"
    
    # 2. Заполняем форму на основном лендинге (БЕЗ перехвата запросов, идет реальная запись в БД)
    page.goto(BASE_URL)
    page.fill("#b2b-name", lead_name)
    page.fill("#b2b-company", f"E2E Company_{unique_id}")
    page.fill("#b2b-email", f"e2e-b2b-{unique_id}@testing.ru")
    page.fill("#b2b-phone", "9000000001")
    page.select_option("#b2b-service", "corporate-training")
    page.fill("#b2b-message", "E2E проверка прохождения лида в админку.")
    page.check("#formB2B input[name='privacy']")
    page.click("#formB2B button[type='submit']")
    
    # Ожидаем успешного экрана на UI
    expect(page.locator("#formSuccess")).to_be_visible()
    
    # 3. Переходим в админ-панель Streamlit
    page.goto(ADMIN_URL)
    
    # Переключаемся на вкладку "Лиды" в боковой панели
    # В Streamlit опции радиокнопки оборачиваются в label
    page.click("label:has-text('🎯 Лиды')")
    
    # Ожидаем отрисовки таблицы лидов
    page.wait_for_timeout(2000) # Даем время загрузиться данным из БД
    
    # Проверяем, что на странице присутствует текст с уникальным именем созданного лида
    expect(page.get_by_text(lead_name)).to_be_attached()

def test_e2e_integration_b2c_form_to_streamlit_admin(page: Page):
    """
    Тест 19: Полный E2E-сценарий (B2C).
    Регистрация лида на лендинге -> Проверка его появления в админ-панели Streamlit.
    """
    unique_id = str(uuid.uuid4())[:8]
    lead_name = f"E2E_B2C_Lead_{unique_id}"
    
    # 1. Заполняем форму B2C
    page.goto(BASE_URL)
    page.click("button[data-tab='b2c']")
    page.fill("#b2c-name", lead_name)
    page.fill("#b2c-email", f"e2e-b2c-{unique_id}@testing.ru")
    page.fill("#b2c-phone", "9000000002")
    page.select_option("#b2c-interest", "web-dev")
    page.fill("#b2c-message", "Интеграционный B2C тест.")
    page.check("#formB2C input[name='privacy']")
    page.click("#formB2C button[type='submit']")
    
    expect(page.locator("#formSuccess")).to_be_visible()
    
    # 2. Проверяем в админке
    page.goto(ADMIN_URL)
    page.click("label:has-text('🎯 Лиды')")
    page.wait_for_timeout(2000)
    
    expect(page.get_by_text(lead_name)).to_be_attached()
