import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from redis import Redis
from dotenv import load_dotenv
import os
import time

# Загружаем переменные окружения из .env
load_dotenv()

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(
    page_title="Sales AI Bot - Админ-панель",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ИНЪЕКЦИЯ СТИЛЕЙ ИЗ ЛЕНДИНГА ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    /* Основной фон и шрифт */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #0a0a0f !important;
        color: #f0f0f5 !important;
    }
    
    /* Скрытие дефолтного хедера Streamlit */
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
    }
    
    /* Стилизация боковой панели (Sidebar) */
    [data-testid="stSidebar"] {
        background-color: #111118 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    
    /* Заголовок с градиентным текстом */
    .gradient-header {
        background: linear-gradient(135deg, #6366f1 0%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        font-size: 2.2rem !important;
        margin-bottom: 1.5rem !important;
        letter-spacing: -0.02em;
    }
    
    /* Стеклянные карточки для KPI метрик */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        padding: 1.2rem 1.5rem !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
        transition: transform 0.3s ease, border-color 0.3s ease, background-color 0.3s ease !important;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px) !important;
        border-color: rgba(99, 102, 241, 0.4) !important;
        background: rgba(255, 255, 255, 0.06) !important;
    }
    
    /* Метрики текст */
    div[data-testid="stMetricLabel"] {
        color: #a0a0b0 !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetricValue"] {
        color: #f0f0f5 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    /* Поля ввода (логин, пароль, селекторы) */
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        background-color: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 8px !important;
        color: #f0f0f5 !important;
        font-family: 'Inter', sans-serif !important;
        transition: border-color 0.3s, box-shadow 0.3s !important;
    }
    
    div[data-testid="stTextInput"] input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
        outline: none !important;
    }
    
    /* Кнопки в стиле лендинга */
    div.stButton > button, div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #6366f1 0%, #06b6d4 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        transition: transform 0.3s, box-shadow 0.3s, opacity 0.3s !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.2) !important;
    }
    div.stButton > button:hover, div[data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.3) !important;
        opacity: 0.95 !important;
    }
    div.stButton > button:active, div[data-testid="stFormSubmitButton"] button:active {
        transform: translateY(1px) !important;
    }
    
    /* Таблицы лидов */
    div[data-testid="stDataFrame"] {
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        background-color: #111118 !important;
        overflow: hidden !important;
    }
    
    /* Контейнер формы входа */
    .login-container {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 3rem !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
        backdrop-filter: blur(8px) !important;
        margin-top: 4rem !important;
    }
    /* Скрытие стандартных границ Streamlit-формы */
    div[data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
        background-color: transparent !important;
    }
    </style>
    
    <!-- Фоновые светящиеся сферы и сетка как на лендинге -->
    <div class="grid-overlay"></div>
    <div class="gradient-orb orb-1"></div>
    <div class="gradient-orb orb-2"></div>
    
    <style>
    .gradient-orb {
        position: fixed;
        width: 600px;
        height: 600px;
        border-radius: 50%;
        filter: blur(150px);
        opacity: 0.12;
        z-index: -1;
        pointer-events: none;
    }
    .orb-1 {
        background: #6366f1;
        top: -10%;
        left: -10%;
    }
    .orb-2 {
        background: #8b5cf6;
        bottom: -10%;
        right: -10%;
    }
    .grid-overlay {
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-image: linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
                          linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
        background-size: 50px 50px;
        z-index: -2;
        pointer-events: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)


def check_password():
    """Возвращает True, если пользователь успешно авторизован."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    # Отрисовка формы входа в центре экрана
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown(
            "<h2 style='text-align: center; background: linear-gradient(135deg, #6366f1 0%, #06b6d4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;'>🤖 Sales AI Admin</h2>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='text-align: center; color: #a0a0b0; font-size: 0.95rem; margin-bottom: 2rem;'>Панель управления отделом продаж</p>",
            unsafe_allow_html=True
        )
        
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Логин", placeholder="Введите имя пользователя")
            password = st.text_input("Пароль", type="password", placeholder="Введите пароль")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Войти в систему", use_container_width=True)
            
            if submit:
                # Очищаем от пробелов и приводим логин к нижнему регистру
                expected_username = os.getenv("ADMIN_USERNAME", "admin").strip()
                expected_password = os.getenv("ADMIN_PASSWORD", "admin123").strip()
                
                clean_user = username.strip()
                clean_pass = password.strip()
                
                if clean_user.lower() == expected_username.lower() and clean_pass == expected_password:
                    st.session_state["authenticated"] = True
                    st.success("Успешный вход! Загрузка панели...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(" Неверный логин или пароль")
        st.markdown('</div>', unsafe_allow_html=True)
                
    return False


if not check_password():
    st.stop()



# --- ПОДКЛЮЧЕНИЕ К БД И REDIS ---
@st.cache_resource
def get_db_engine():
    """Создаем движок БД (кэшируется, чтобы не пересоздавать при каждом клике)."""
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/sales_bot")
    sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    return create_engine(sync_url, pool_pre_ping=True)

@st.cache_resource
def get_redis_client():
    """Создаем клиент Redis."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return Redis.from_url(redis_url, decode_responses=True)

engine = get_db_engine()
redis_client = get_redis_client()

# --- БОКОВАЯ ПАНЕЛЬ (НАВИГАЦИЯ) ---
st.sidebar.title("🤖 Sales AI Admin")
page = st.sidebar.radio(
    "Перейти к разделу:",
    ["📊 Дашборд", "💬 История диалогов", "🎯 Лиды", "⚙️ Кэш и настройки"]
)


st.sidebar.markdown("---")
st.sidebar.info("Версия MVP: 1.0.0\nСтатус системы: 🟢 Активен")

# --- РАЗДЕЛ 1: ДАШБОРД ---
if page == "📊 Дашборд":
    st.markdown('<h1 class="gradient-header">📊 Дашборд эффективности бота</h1>', unsafe_allow_html=True)
    
    # Запрос метрик из БД
    try:
        with engine.connect() as conn:
            total_dialogs = conn.execute(text("SELECT COUNT(*) FROM dialogs")).scalar()
            total_leads = conn.execute(text("SELECT COUNT(*) FROM leads")).scalar()
            total_users = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
            
            # Распределение по типам клиентов
            client_types = pd.read_sql(
                text("SELECT client_type, COUNT(*) as count FROM users GROUP BY client_type"), 
                conn
            )
            
            # Активность по дням (последние 7 дней)
            daily_activity = pd.read_sql(
                text("SELECT DATE(started_at) as date, COUNT(*) as count FROM dialogs GROUP BY DATE(started_at) ORDER BY date DESC LIMIT 7"),
                conn
            )
    except Exception as e:
        st.error(f"Ошибка подключения к БД: {e}")
        st.stop()

    # KPI Карточки
    col1, col2, col3 = st.columns(3)
    col1.metric(" Всего пользователей", total_users)
    col2.metric("💬 Всего диалогов", total_dialogs)
    col3.metric(" Собранных лидов", total_leads)

    st.markdown("---")
    
    # Графики
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader(" Активность за последние 7 дней")
        if not daily_activity.empty:
            fig = px.bar(daily_activity, x='date', y='count', color='count', color_continuous_scale='Viridis')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Нет данных за последние дни")
            
    with col_chart2:
        st.subheader("🏢 Распределение клиентов")
        if not client_types.empty:
            fig = px.pie(client_types, values='count', names='client_type', title="МСБ vs Энтерпрайз")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Нет данных о клиентах")

# --- РАЗДЕЛ 2: ИСТОРИЯ ДИАЛОГОВ ---
elif page == "💬 История диалогов":
    st.markdown('<h1 class="gradient-header">💬 История диалогов</h1>', unsafe_allow_html=True)
    
    try:
        with engine.connect() as conn:
            # Получаем последние 50 диалогов
            query = """
                SELECT d.session_id, d.started_at, d.status, u.external_id, u.client_type, 
                       COUNT(m.id) as message_count
                FROM dialogs d
                JOIN users u ON d.user_id = u.id
                LEFT JOIN messages m ON d.id = m.dialog_id
                GROUP BY d.id, u.external_id, u.client_type
                ORDER BY d.started_at DESC
                LIMIT 50
            """
            dialogs_df = pd.read_sql(text(query), conn)
            
        st.dataframe(dialogs_df, use_container_width=True, hide_index=True)
        
        # Детальный просмотр
        st.subheader("🔍 Просмотр конкретного диалога")
        selected_session = st.selectbox("Выберите сессию:", dialogs_df['session_id'].tolist())
        
        if selected_session:
            with engine.connect() as conn:
                messages_query = text("""
                    SELECT m.role, m.content, m.created_at 
                    FROM messages m
                    JOIN dialogs d ON m.dialog_id = d.id
                    WHERE d.session_id = :session_id
                    ORDER BY m.created_at ASC
                """)
                messages_df = pd.read_sql(messages_query, conn, params={"session_id": selected_session})
            
            for _, row in messages_df.iterrows():
                if row['role'] == 'user':
                    st.markdown(f"👤 **Клиент:** {row['content']}")
                else:
                    st.markdown(f"🤖 **Бот:** {row['content']}")
                st.caption(f" {row['created_at']}")
                st.markdown("---")
                
    except Exception as e:
        st.error(f"Ошибка загрузки диалогов: {e}")

# --- РАЗДЕЛ 3: ЛИДЫ ---
elif page == "🎯 Лиды":
    st.markdown('<h1 class="gradient-header">🎯 Квалифицированные лиды</h1>', unsafe_allow_html=True)
    
    try:
        with engine.connect() as conn:
            leads_query = """
                SELECT l.id, l.status, l.client_name, l.client_phone, l.client_email,
                       l.interested_product, l.client_comment, l.created_at, 
                       u.external_id, u.client_type
                FROM leads l
                JOIN users u ON l.user_id = u.id
                ORDER BY l.created_at DESC
            """
            leads_df = pd.read_sql(text(leads_query), conn)
            
        if leads_df.empty:
            st.warning("Пока нет собранных лидов. Бот продолжает квалификацию!")
        else:
            st.dataframe(leads_df, use_container_width=True, hide_index=True)
            
            # Экспорт в CSV
            csv = leads_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Скачать лиды в CSV",
                data=csv,
                file_name='leads_export.csv',
                mime='text/csv',
            )
    except Exception as e:
        st.error(f"Ошибка загрузки лидов: {e}")

# --- РАЗДЕЛ 4: КЭШ И НАСТРОЙКИ ---
elif page == "⚙️ Кэш и настройки":
    st.markdown('<h1 class="gradient-header">⚙️ Управление кэшем и системой</h1>', unsafe_allow_html=True)
    
    st.subheader("📊 Статистика Redis кэша")
    try:
        # Считаем ключи кэша
        cursor = 0
        cache_keys = []
        while True:
            cursor, keys = redis_client.scan(cursor=cursor, match="cache:*", count=100)
            cache_keys.extend([k for k in keys if not k.endswith(':hits')])
            if cursor == 0:
                break
        
        col1, col2 = st.columns(2)
        col1.metric("📦 Закешированных ответов", len(cache_keys))
        
        # Считаем хиты
        total_hits = 0
        for key in cache_keys:
            hits = redis_client.get(f"{key}:hits")
            if hits:
                total_hits += int(hits)
        col2.metric(" Всего обращений к кэшу", total_hits)
        
    except Exception as e:
        st.error(f"Ошибка подключения к Redis: {e}")

    st.markdown("---")
    
    st.subheader("🧹 Очистка кэша")
    st.warning("️ Это действие удалит все закешированные ответы бота. Первые запросы после очистки будут обрабатываться дольше.")
    
    if st.button("🗑️ Очистить весь кэш", type="primary"):
        try:
            cursor = 0
            while True:
                cursor, keys = redis_client.scan(cursor=cursor, match="cache:*", count=100)
                if keys:
                    redis_client.delete(*keys)
                if cursor == 0:
                    break
            st.success("✅ Кэш успешно очищен!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Ошибка при очистке: {e}")
