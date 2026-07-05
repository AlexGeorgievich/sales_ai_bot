import pytest
import os
import uuid
import allure
from playwright.sync_api import Page, expect

# Базовый URL страницы лендинга и админ-панели
BASE_URL = os.getenv("PLAYWRIGHT_BASE_URL", "http://localhost")
ADMIN_URL = os.getenv("PLAYWRIGHT_ADMIN_URL", "http://localhost:8501")

# ==========================================
# 1. ТЕСТЫ ЗАГРУЗКИ, НАВИГАЦИИ И АДАПТИВНОСТИ
# ==========================================

@allure.epic("Лендинг NexusCode")
@allure.feature("Интерфейс и навигация")
@allure.story("Базовая загрузка страницы")
@allure.severity(allure.severity_level.BLOCKER)
def test_landing_page_load(page: Page):
    """Тест 1: Проверка базовой загрузки лендинга, логотипа и hero-секции."""
    with allure.step("Открыть главную страницу лендинга"):
        page.goto(BASE_URL)
    
    with allure.step("Проверить title страницы"):
        expect(page).to_have_title("NexusCode — Разработка. Внедрение. Обучение.")
        
    with allure.step("Проверить видимость навбара и текст логотипа"):
        expect(page.locator("nav.navbar")).to_be_visible()
        expect(page.locator("nav.navbar .logo-text")).to_have_text("NexusCode")
        
    with allure.step("Проверить видимость секции Hero и главного заголовка H1"):
        expect(page.locator("section#hero")).to_be_visible()
        expect(page.locator("h1")).to_contain_text("Разработка. Внедрение.")


@allure.epic("Лендинг NexusCode")
@allure.feature("Интерфейс и навигация")
@allure.story("Якорная навигация")
@allure.severity(allure.severity_level.NORMAL)
def test_landing_navigation_scroll(page: Page):
    """Тест 2: Проверка навигационных якорных ссылок на лендинге."""
    with allure.step("Открыть главную страницу"):
        page.goto(BASE_URL)
        
    with allure.step("Нажать на ссылку 'Услуги' в шапке"):
        page.click("nav.navbar a[href='#services']")
        
    with allure.step("Проверить, что секция #services видна во вьюпорте"):
        expect(page.locator("section#services")).to_be_in_viewport()


@allure.epic("Лендинг NexusCode")
@allure.feature("Интерфейс и навигация")
@allure.story("Мобильная адаптивность шапки")
@allure.severity(allure.severity_level.CRITICAL)
def test_landing_mobile_hamburger_menu(page: Page):
    """Тест 3: Проверка мобильной адаптивности навигационного меню (бургер-меню)."""
    with allure.step("Задать мобильное разрешение вьюпорта (iPhone 12)"):
        page.set_viewport_size({"width": 375, "height": 812})
        
    with allure.step("Открыть главную страницу"):
        page.goto(BASE_URL)
    
    with allure.step("Убедиться, что бургер-кнопка видна, а меню скрыто"):
        burger = page.locator("button#burger")
        expect(burger).to_be_visible()
        
    with allure.step("Кликнуть на бургер-меню"):
        burger.click()
        
    with allure.step("Проверить, что список навигационных ссылок стал видимым"):
        expect(page.locator("ul#navLinks")).to_be_visible()

# ==========================================
# 2. ТЕСТЫ ВКЛАДОК И ВАЛИДАЦИИ ФОРМ
# ==========================================

@allure.epic("Лендинг NexusCode")
@allure.feature("Формы регистрации лидов")
@allure.story("Переключение типов клиентов")
@allure.severity(allure.severity_level.NORMAL)
def test_form_tabs_switching(page: Page):
    """Тест 4: Переключение вкладок B2B и B2C форм."""
    with allure.step("Открыть главную страницу"):
        page.goto(BASE_URL)
    
    with allure.step("Проверить, что по умолчанию активна форма B2B"):
        expect(page.locator("#formB2B")).to_be_visible()
        expect(page.locator("#formB2C")).to_have_class(r"contact-form hidden")
    
    with allure.step("Переключиться на вкладку B2C (Частные лица)"):
        page.click("button[data-tab='b2c']")
        
    with allure.step("Проверить видимость формы B2C и скрытие B2B"):
        expect(page.locator("#formB2C")).to_be_visible()
        expect(page.locator("#formB2B")).to_have_class(r"contact-form hidden")

@allure.epic("Лендинг NexusCode")
@allure.feature("Формы регистрации лидов")
@allure.story("Валидация формы B2B")
@allure.severity(allure.severity_level.CRITICAL)
def test_b2b_form_validation_required_fields(page: Page):
    """Тест 5: HTML5 валидация обязательного поля Имя в форме B2B."""
    with allure.step("Открыть главную страницу"):
        page.goto(BASE_URL)
        
    with allure.step("Очистить поле имени и отправить форму"):
        page.locator("#b2b-name").fill("")
        page.click("#formB2B button[type='submit']")
    
    with allure.step("Проверить невалидность поля имени"):
        is_valid = page.evaluate("document.getElementById('b2b-name').checkValidity()")
        assert is_valid is False

@allure.epic("Лендинг NexusCode")
@allure.feature("Формы регистрации лидов")
@allure.story("Валидация формы B2B")
@allure.severity(allure.severity_level.NORMAL)
def test_b2b_form_validation_email(page: Page):
    """Тест 6: Валидация формата Email в форме B2B."""
    page.goto(BASE_URL)
    with allure.step("Заполнить тестовые данные и ввести некорректный email"):
        page.fill("#b2b-name", "Тест")
        page.fill("#b2b-company", "ТестКомпани")
        page.fill("#b2b-email", "invalid-email")
        page.click("#formB2B button[type='submit']")
    
    with allure.step("Проверить, что поле email не прошло HTML5-валидацию"):
        is_valid = page.evaluate("document.getElementById('b2b-email').checkValidity()")
        assert is_valid is False

@allure.epic("Лендинг NexusCode")
@allure.feature("Формы регистрации лидов")
@allure.story("Валидация формы B2B")
@allure.severity(allure.severity_level.NORMAL)
def test_b2b_form_validation_privacy(page: Page):
    """Тест 7: Валидация обязательного согласия с политикой конфиденциальности (B2B)."""
    page.goto(BASE_URL)
    with allure.step("Заполнить форму B2B и снять чекбокс согласия"):
        page.fill("#b2b-name", "Иван")
        page.fill("#b2b-company", "Тест")
        page.fill("#b2b-email", "test@test.ru")
        page.uncheck("#formB2B input[name='privacy']")
        page.click("#formB2B button[type='submit']")
    
    with allure.step("Проверить, что согласие помечено как обязательное"):
        is_valid = page.evaluate("document.querySelector('#formB2B input[name=\"privacy\"]').checkValidity()")
        assert is_valid is False

@allure.epic("Лендинг NexusCode")
@allure.feature("Формы регистрации лидов")
@allure.story("Маска ввода телефона")
@allure.severity(allure.severity_level.NORMAL)
def test_b2b_phone_mask(page: Page):
    """Тест 8: Маска ввода телефона формы B2B (+7 (XXX) XXX-XX-XX)."""
    page.goto(BASE_URL)
    with allure.step("Ввести цифры телефона без форматирования"):
        phone_input = page.locator("#b2b-phone")
        phone_input.fill("9991234567")
        
    with allure.step("Проверить автоматическое форматирование маски"):
        expect(phone_input).to_have_value("+7 (999) 123-45-67")

@allure.epic("Лендинг NexusCode")
@allure.feature("Формы регистрации лидов")
@allure.story("Валидация формы B2C")
@allure.severity(allure.severity_level.CRITICAL)
def test_b2c_form_validation_required_fields(page: Page):
    """Тест 9: HTML5 валидация обязательного поля Имя в форме B2C."""
    page.goto(BASE_URL)
    with allure.step("Переключиться на вкладку B2C"):
        page.click("button[data-tab='b2c']")
        
    with allure.step("Очистить имя B2C и отправить"):
        page.locator("#b2c-name").fill("")
        page.click("#formB2C button[type='submit']")
    
    with allure.step("Проверить невалидность имени"):
        is_valid = page.evaluate("document.getElementById('b2c-name').checkValidity()")
        assert is_valid is False

@allure.epic("Лендинг NexusCode")
@allure.feature("Формы регистрации лидов")
@allure.story("Валидация формы B2C")
@allure.severity(allure.severity_level.NORMAL)
def test_b2c_form_validation_email(page: Page):
    """Тест 10: Валидация формата Email в форме B2C."""
    page.goto(BASE_URL)
    page.click("button[data-tab='b2c']")
    with allure.step("Ввести некорректный email в форму B2C"):
        page.fill("#b2c-name", "Алексей")
        page.fill("#b2c-email", "notanemail")
        page.click("#formB2C button[type='submit']")
    
    with allure.step("Проверить невалидность email"):
        is_valid = page.evaluate("document.getElementById('b2c-email').checkValidity()")
        assert is_valid is False

@allure.epic("Лендинг NexusCode")
@allure.feature("Формы регистрации лидов")
@allure.story("Валидация формы B2C")
@allure.severity(allure.severity_level.NORMAL)
def test_b2c_form_validation_privacy(page: Page):
    """Тест 11: Валидация согласия с политикой конфиденциальности (B2C)."""
    page.goto(BASE_URL)
    page.click("button[data-tab='b2c']")
    with allure.step("Заполнить форму B2C и снять флаг согласия"):
        page.fill("#b2c-name", "Алексей")
        page.fill("#b2c-email", "b2c@test.ru")
        page.uncheck("#formB2C input[name='privacy']")
        page.click("#formB2C button[type='submit']")
    
    with allure.step("Проверить невалидность чекбокса"):
        is_valid = page.evaluate("document.querySelector('#formB2C input[name=\"privacy\"]').checkValidity()")
        assert is_valid is False

@allure.epic("Лендинг NexusCode")
@allure.feature("Формы регистрации лидов")
@allure.story("Маска ввода телефона")
@allure.severity(allure.severity_level.NORMAL)
def test_b2c_phone_mask(page: Page):
    """Тест 12: Маска ввода телефона формы B2C."""
    page.goto(BASE_URL)
    page.click("button[data-tab='b2c']")
    with allure.step("Ввести цифры телефона в форму B2C"):
        phone_input = page.locator("#b2c-phone")
        phone_input.fill("9001112233")
        
    with allure.step("Проверить маску ввода телефона"):
        expect(phone_input).to_have_value("+7 (900) 111-22-33")

# ==========================================
# 3. ТЕСТЫ ОТПРАВКИ И СТРУКТУРЫ PAYLOAD
# ==========================================

@allure.epic("Лендинг NexusCode")
@allure.feature("Формы регистрации лидов")
@allure.story("Отправка формы B2B (Mock API)")
@allure.severity(allure.severity_level.CRITICAL)
def test_b2b_submission_payload_with_mock(page: Page):
    """Тест 13: Проверка структуры отправляемого JSON-payload для формы B2B."""
    page.goto(BASE_URL)
    captured_payload = {}
    
    with allure.step("Настроить перехват POST-запросов к /chat/leads"):
        def handle_route(route):
            nonlocal captured_payload
            request = route.request
            if request.method == "POST" and "chat/leads" in request.url:
                captured_payload.update(request.post_data_json)
            route.fulfill(status=201, json={"status": "success", "id": 1})
        page.route("**/chat/leads", handle_route)
    
    with allure.step("Заполнить все поля формы B2B"):
        page.fill("#b2b-name", "Иван Иванов")
        page.fill("#b2b-company", "ООО Ромашка")
        page.fill("#b2b-email", "romashka@b2b.ru")
        page.fill("#b2b-phone", "9555555555")
        page.select_option("#b2b-service", "implementation")
        page.fill("#b2b-message", "Требуется CRM")
        page.check("#formB2B input[name='privacy']")
    
    with allure.step("Отправить форму"):
        page.click("#formB2B button[type='submit']")
    
    with allure.step("Проверить отображение экрана об успешной отправке"):
        expect(page.locator("#formSuccess")).to_be_visible()
    
    with allure.step("Проверить корректность структуры и значений отправленного JSON"):
        assert captured_payload["client_name"] == "Иван Иванов"
        assert captured_payload["client_email"] == "romashka@b2b.ru"
        assert captured_payload["client_phone"] == "+7 (955) 555-55-55"
        assert captured_payload["interested_product"] == "implementation"
        assert captured_payload["client_type"] == "enterprise"
        assert "ООО Ромашка" in captured_payload["client_comment"]

@allure.epic("Лендинг NexusCode")
@allure.feature("Формы регистрации лидов")
@allure.story("Отправка формы B2C (Mock API)")
@allure.severity(allure.severity_level.CRITICAL)
def test_b2c_submission_payload_with_mock(page: Page):
    """Тест 14: Проверка структуры отправляемого JSON-payload для формы B2C."""
    page.goto(BASE_URL)
    page.click("button[data-tab='b2c']")
    captured_payload = {}
    
    with allure.step("Настроить перехват POST-запросов к /chat/leads"):
        def handle_route(route):
            nonlocal captured_payload
            request = route.request
            if request.method == "POST" and "chat/leads" in request.url:
                captured_payload.update(request.post_data_json)
            route.fulfill(status=201, json={"status": "success", "id": 2})
        page.route("**/chat/leads", handle_route)
    
    with allure.step("Заполнить все поля формы B2C"):
        page.fill("#b2c-name", "Анна Смирнова")
        page.fill("#b2c-email", "anna@example.com")
        page.fill("#b2c-phone", "9007778899")
        page.select_option("#b2c-interest", "ai-dev")
        page.fill("#b2c-message", "Интересует курс")
        page.check("#formB2C input[name='privacy']")
    
    with allure.step("Отправить форму B2C"):
        page.click("#formB2C button[type='submit']")
        
    with allure.step("Проверить отображение экрана об успешной отправке"):
        expect(page.locator("#formSuccess")).to_be_visible()
    
    with allure.step("Проверить корректность структуры и значений отправленного JSON B2C"):
        assert captured_payload["client_name"] == "Анна Смирнова"
        assert captured_payload["client_email"] == "anna@example.com"
        assert captured_payload["client_phone"] == "+7 (900) 777-88-99"
        assert captured_payload["interested_product"] == "ai-dev"
        assert captured_payload["client_comment"] == "Интересует курс"
        assert captured_payload["client_type"] == "msb"

# ==========================================
# 4. ТЕСТЫ ЧАТ-БОТА (ИНТЕРАКТИВНЫЙ ВИДЖЕТ)
# ==========================================

@allure.epic("Чат-бот Ассистент")
@allure.feature("Виджет чата")
@allure.story("Открытие и закрытие окна")
@allure.severity(allure.severity_level.NORMAL)
def test_chat_widget_toggle_ui(page: Page):
    """Тест 15: Открытие и закрытие виджета чата."""
    page.goto(BASE_URL)
    
    toggle_btn = page.locator("#sales-ai-toggle")
    chat_container = page.locator("#sales-ai-chat")
    close_btn = page.locator("#sales-ai-close")
    
    with allure.step("Проверить видимость кнопки открытия чата"):
        expect(toggle_btn).to_be_visible()
        expect(chat_container).not_to_have_class("open")
    
    with allure.step("Нажать кнопку открытия чата"):
        toggle_btn.click()
        expect(chat_container).to_have_class(r"sales-ai-chat-container open")
    
    with allure.step("Нажать кнопку закрытия чата"):
        close_btn.click()
        expect(chat_container).not_to_have_class("open")

@allure.epic("Чат-бот Ассистент")
@allure.feature("Виджет чата")
@allure.story("Приветственное сообщение")
@allure.severity(allure.severity_level.NORMAL)
def test_chat_widget_welcome_message(page: Page):
    """Тест 16: Отображение приветственного сообщения при открытии чата."""
    page.goto(BASE_URL)
    with allure.step("Открыть окно чат-виджета"):
        page.click("#sales-ai-toggle")
    
    with allure.step("Проверить наличие приветственного сообщения от бота"):
        welcome_bubble = page.locator("#sales-ai-messages .sales-ai-message.bot .sales-ai-message-bubble")
        expect(welcome_bubble).to_be_visible()
        expect(welcome_bubble).to_contain_text("Здравствуйте!")

@allure.epic("Чат-бот Ассистент")
@allure.feature("Виджет чата")
@allure.story("Отправка сообщений боту (Mock API)")
@allure.severity(allure.severity_level.CRITICAL)
def test_chat_widget_send_message_mock(page: Page):
    """Тест 17: Имитация отправки сообщения и получения ответа от ИИ."""
    page.goto(BASE_URL)
    with allure.step("Открыть окно чата"):
        page.click("#sales-ai-toggle")
    
    with allure.step("Настроить перехват запросов ИИ к /chat/message"):
        page.route("**/chat/message", lambda route: route.fulfill(
            status=200, 
            json={"response": "Я могу помочь с интеграцией GigaChat API."}
        ))
    
    with allure.step("Ввести вопрос и нажать Enter"):
        page.fill("#sales-ai-input", "Расскажи про GigaChat")
        page.press("#sales-ai-input", "Enter")
    
    with allure.step("Проверить, что отправленное сообщение появилось на экране"):
        expect(page.locator("#sales-ai-messages .sales-ai-message.user .sales-ai-message-bubble")).to_contain_text("Расскажи про GigaChat")
    
    with allure.step("Проверить получение и рендеринг ответа бота"):
        bot_messages = page.locator("#sales-ai-messages .sales-ai-message.bot .sales-ai-message-bubble")
        expect(bot_messages).to_have_count(2)
        expect(bot_messages.nth(1)).to_have_text("Я могу помочь с интеграцией GigaChat API.")

# ==========================================
# 5. ИНТЕГРАЦИОННЫЕ E2E СЦЕНАРИИ
# ==========================================

@allure.epic("Сквозные E2E сценарии")
@allure.feature("Интеграция Лендинг -> БД -> Админка")
@allure.story("Прохождение лида B2B")
@allure.severity(allure.severity_level.CRITICAL)
def test_e2e_integration_b2b_form_to_streamlit_admin(page: Page):
    """Тест 18: Полный E2E-сценарий (B2B). Регистрация на лендинге -> Проверка в админке."""
    unique_id = str(uuid.uuid4())[:8]
    lead_name = f"E2E_B2B_Lead_{unique_id}"
    
    with allure.step("Шаг 1: Заполнить форму B2B реальными данными на лендинге"):
        page.goto(BASE_URL)
        page.fill("#b2b-name", lead_name)
        page.fill("#b2b-company", f"E2E Company_{unique_id}")
        page.fill("#b2b-email", f"e2e-b2b-{unique_id}@testing.ru")
        page.fill("#b2b-phone", "9000000001")
        page.select_option("#b2b-service", "corporate-training")
        page.fill("#b2b-message", "E2E проверка прохождения лида в админку.")
        page.check("#formB2B input[name='privacy']")
        page.click("#formB2B button[type='submit']")
        expect(page.locator("#formSuccess")).to_be_visible()
    
    with allure.step("Шаг 2: Перейти в админ-панель Streamlit"):
        page.goto(ADMIN_URL)
        
    with allure.step("Шаг 3: Открыть вкладку 'Лиды'"):
        page.click("label:has-text('🎯 Лиды')")
        page.wait_for_timeout(2000) # Даем время на опрос БД
        
    with allure.step("Шаг 4: Проверить, что имя лида присутствует в DOM таблицы"):
        expect(page.get_by_text(lead_name)).to_be_attached()

@allure.epic("Сквозные E2E сценарии")
@allure.feature("Интеграция Лендинг -> БД -> Админка")
@allure.story("Прохождение лида B2C")
@allure.severity(allure.severity_level.CRITICAL)
def test_e2e_integration_b2c_form_to_streamlit_admin(page: Page):
    """Тест 19: Полный E2E-сценарий (B2C). Регистрация на лендинге -> Проверка в админке."""
    unique_id = str(uuid.uuid4())[:8]
    lead_name = f"E2E_B2C_Lead_{unique_id}"
    
    with allure.step("Шаг 1: Заполнить форму B2C реальными данными на лендинге"):
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
    
    with allure.step("Шаг 2: Перейти в админ-панель Streamlit"):
        page.goto(ADMIN_URL)
        
    with allure.step("Шаг 3: Перейти в раздел 'Лиды'"):
        page.click("label:has-text('🎯 Лиды')")
        page.wait_for_timeout(2000)
        
    with allure.step("Шаг 4: Убедиться в наличии записи лида"):
        expect(page.get_by_text(lead_name)).to_be_attached()
