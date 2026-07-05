import pytest
import os
from playwright.sync_api import Page, expect

# Базовый URL страницы лендинга. По умолчанию тестируем локально запущенный в Docker Nginx
BASE_URL = os.getenv("PLAYWRIGHT_BASE_URL", "http://localhost")

def test_landing_page_load(page: Page):
    """
    Тест 1: Проверка загрузки лендинга, присутствия заголовка и основных элементов.
    """
    page.goto(BASE_URL)
    
    # Проверяем заголовок вкладки браузера (title)
    expect(page).to_have_title("NexusCode — Разработка. Внедрение. Обучение.")
    
    # Проверяем наличие логотипа и навигационной панели
    expect(page.locator("nav.navbar")).to_be_visible()
    expect(page.locator("nav.navbar .logo-text")).to_have_text("NexusCode")
    
    # Проверяем видимость секции Hero
    expect(page.locator("section#hero")).to_be_visible()
    expect(page.locator("h1")).to_contain_text("Разработка. Внедрение.")


def test_form_tabs_switching(page: Page):
    """
    Тест 2: Проверка переключения вкладок форм B2B и B2C.
    """
    page.goto(BASE_URL)
    
    # По умолчанию форма B2B должна быть видима, а B2C — скрыта
    expect(page.locator("#formB2B")).to_be_visible()
    expect(page.locator("#formB2C")).to_have_class(r"contact-form hidden")
    
    # Переключаемся на вкладку B2C (Для частных лиц)
    page.click("button[data-tab='b2c']")
    
    # Проверяем, что форма B2C теперь видима, а B2B — скрыта
    expect(page.locator("#formB2C")).to_be_visible()
    expect(page.locator("#formB2B")).to_have_class(r"contact-form hidden")
    
    # Переключаемся обратно на B2B (Для бизнеса)
    page.click("button[data-tab='b2b']")
    
    # Проверяем состояние
    expect(page.locator("#formB2B")).to_be_visible()
    expect(page.locator("#formB2C")).to_have_class(r"contact-form hidden")


def test_phone_mask_formatting(page: Page):
    """
    Тест 3: Проверка автоматического форматирования маски телефона при вводе.
    """
    page.goto(BASE_URL)
    
    # Вводим цифры в поле телефона формы B2B
    phone_input = page.locator("#b2b-phone")
    phone_input.fill("9998887766")
    
    # Проверяем, что маска телефона отформатировала ввод
    # Ожидается: +7 (999) 888-77-66
    expect(phone_input).to_have_value("+7 (999) 888-77-66")


def test_b2b_lead_submission(page: Page):
    """
    Тест 4: Проверка заполнения и успешной отправки формы B2B (Для бизнеса).
    Проверяем отправляемый JSON-payload в POST-запросе и показ сообщения об успехе.
    """
    page.goto(BASE_URL)
    
    # Объект для перехвата отправленного payload
    captured_payload = {}
    
    # Настраиваем перехват POST запроса к API сохранения лидов
    def handle_route(route):
        nonlocal captured_payload
        request = route.request
        if request.method == "POST" and "chat/leads" in request.url:
            captured_payload.update(request.post_data_json)
        route.fulfill(status=201, json={"status": "success", "message": "Lead saved successfully"})
        
    page.route("**/chat/leads", handle_route)
    
    # Заполняем форму B2B
    page.fill("#b2b-name", "Иван Иванов")
    page.fill("#b2b-company", "Тестовая Компания B2B")
    page.fill("#b2b-email", "b2b-client@test.ru")
    page.fill("#b2b-phone", "9112223344")
    page.select_option("#b2b-service", "development")
    page.fill("#b2b-message", "Необходима разработка AI чат-бота для нашего сайта.")
    
    # Отмечаем чекбокс согласия
    page.check("#formB2B input[name='privacy']")
    
    # Отправляем форму
    page.click("#formB2B button[type='submit']")
    
    # Проверяем, что форма скрылась, а сообщение об успехе появилось
    expect(page.locator("#formB2B")).to_have_class(r"contact-form hidden")
    expect(page.locator("#formSuccess")).to_be_visible()
    
    # Проверяем структуру и наполнение отправленного на бэкенд JSON-payload
    assert captured_payload.get("client_name") == "Иван Иванов"
    assert captured_payload.get("client_email") == "b2b-client@test.ru"
    assert captured_payload.get("client_phone") == "+7 (911) 222-33-44"
    assert captured_payload.get("interested_product") == "development"
    assert "Тестовая Компания B2B" in captured_payload.get("client_comment")
    assert "Необходима разработка AI чат-бота" in captured_payload.get("client_comment")
    assert captured_payload.get("client_type") == "enterprise"


def test_b2c_lead_submission(page: Page):
    """
    Тест 5: Проверка заполнения и успешной отправки формы B2C (Для частных лиц).
    Проверяем отправляемый JSON-payload в POST-запросе и показ сообщения об успехе.
    """
    page.goto(BASE_URL)
    
    # Переключаемся на B2C
    page.click("button[data-tab='b2c']")
    
    captured_payload = {}
    
    # Перехват запроса к API
    def handle_route(route):
        nonlocal captured_payload
        request = route.request
        if request.method == "POST" and "chat/leads" in request.url:
            captured_payload.update(request.post_data_json)
        route.fulfill(status=201, json={"status": "success", "message": "Lead saved successfully"})
        
    page.route("**/chat/leads", handle_route)
    
    # Заполняем форму B2C
    page.fill("#b2c-name", "Алексей Петров")
    page.fill("#b2c-email", "b2c-client@test.ru")
    page.fill("#b2c-phone", "9223334455")
    page.select_option("#b2c-interest", "vibe-pro")
    page.fill("#b2c-message", "Хочу записаться на курс продвинутого вайб-кодинга.")
    
    # Согласие
    page.check("#formB2C input[name='privacy']")
    
    # Отправка
    page.click("#formB2C button[type='submit']")
    
    # Проверяем успешный результат на UI
    expect(page.locator("#formB2C")).to_have_class(r"contact-form hidden")
    expect(page.locator("#formSuccess")).to_be_visible()
    
    # Проверяем payload запроса
    assert captured_payload.get("client_name") == "Алексей Петров"
    assert captured_payload.get("client_email") == "b2c-client@test.ru"
    assert captured_payload.get("client_phone") == "+7 (922) 333-44-55"
    assert captured_payload.get("interested_product") == "vibe-pro"
    assert captured_payload.get("client_comment") == "Хочу записаться на курс продвинутого вайб-кодинга."
    assert captured_payload.get("client_type") == "msb"
