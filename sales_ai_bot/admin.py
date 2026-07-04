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

# --- ПОДКЛЮЧЕНИЕ К БД И REDIS ---
@st.cache_resource
def get_db_engine():
    """Создаем движок БД (кэшируется, чтобы не пересоздавать при каждом клике)."""
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/sales_bot")
    # Для pandas используем psycopg2, если asyncpg не поддерживается напрямую для read_sql
    # В реальном проекте лучше использовать синхронный драйвер для админки
    sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    return create_engine(sync_url)

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
    st.title("📊 Дашборд эффективности бота")
    
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
    st.title("💬 История диалогов")
    
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
    st.title("🎯 Квалифицированные лиды")
    
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
    st.title("️ Управление кэшем и системой")
    
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
