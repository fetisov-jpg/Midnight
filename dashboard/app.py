# dashboard/app.py
import streamlit as st
import aiohttp
import asyncio
import os
import time
import pandas as pd
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

# Настройки API
API_BASE = "http://localhost:8000/api/v1"

# Настройка страницы
st.set_page_config(
    page_title="Midnight Dashboard",
    page_icon=":crescent_moon:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Заголовок
st.title("Midnight API Dashboard")
st.caption(f"Connected to: {API_BASE}")

# --- Sidebar ---
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Select section",
        ["Main", "PostgreSQL", "Users", "Activity"]
    )

    st.divider()

    # Настройка автообновления
    auto_refresh = st.checkbox("Auto-refresh (5 sec)", value=True)
    st.caption("Updates every 5 seconds")

    st.divider()
    st.caption(f"API Version: 0.1.0")
    st.caption(f"Mode: {'Production' if not os.getenv('DEBUG') else 'Development'}")

# --- Инициализация состояния ---
if "selected_table" not in st.session_state:
    st.session_state.selected_table = None

# Если выбранная таблица есть, но мы не на странице PostgreSQL - сбрасываем
if st.session_state.selected_table and page != "PostgreSQL":
    st.session_state.selected_table = None

# --- Асинхронная функция для запросов ---
async def fetch_api(endpoint: str):
    """Выполняет запрос к API"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE}{endpoint}") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {"error": f"HTTP {resp.status}", "detail": await resp.text()}
        except Exception as e:
            return {"error": str(e)}

# --- Функция-обёртка для синхронного вызова ---
def fetch(endpoint: str):
    """Синхронная обёртка для вызова асинхронной функции"""
    return asyncio.run(fetch_api(endpoint))

# --- Main page ---
if page == "Main":
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("API Status", "Online")

    with col2:
        # Проверка БД
        result = fetch("/postgres/db-test")
        if result and "status" in result:
            status = "Connected" if result.get("status") == "ok" else "Error"
            st.metric("PostgreSQL", status)
        else:
            st.metric("PostgreSQL", "Unavailable")

    with col3:
        # Количество пользователей
        users = fetch("/postgres/users")
        if users and isinstance(users, dict) and "users" in users:
            count = len(users["users"])
            st.metric("Users", count)
        else:
            st.metric("Users", "0")

    # Проверка версии
    st.subheader("System Information")

    version = fetch("/postgres/check-version")
    if version and "version" in version:
        st.success(f"PostgreSQL: {version['version'][:50]}...")
    else:
        st.error("Failed to get PostgreSQL version")

    # Активные процессы
    processes = fetch("/postgres/requests")
    if processes and "requests" in processes:
        st.subheader(f"Active processes: {len(processes['requests'])}")
        if processes['requests']:
            df = pd.DataFrame(processes['requests'])
            st.dataframe(df, width='stretch')
    else:
        st.info("No active processes")

# --- PostgreSQL ---
elif page == "PostgreSQL":
    st.header("PostgreSQL Management")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Show all tables", width='stretch'):
            tables = fetch("/postgres/tables")
            if tables:
                if isinstance(tables, list):
                    df = pd.DataFrame(tables)
                else:
                    df = pd.DataFrame(tables.get("tables", []))
                st.dataframe(df, width='stretch')
                st.caption(f"Total: {len(df)} tables")
            else:
                st.warning("No tables found")

    with col2:
        if st.button("Show databases", width='stretch'):
            databases = fetch("/postgres/databases")
            if databases:
                if isinstance(databases, list):
                    df = pd.DataFrame(databases)
                elif isinstance(databases, dict) and "databases" in databases:
                    df = pd.DataFrame(databases["databases"])
                else:
                    df = pd.DataFrame([databases])
                st.dataframe(df, width='stretch')
                st.caption(f"Total: {len(df)} databases")
            else:
                st.warning("No databases found")

    # Всегда показываем таблицы
    st.subheader("Tables list")
    tables = fetch("/postgres/tables")
    if tables:
        if isinstance(tables, list):
            df = pd.DataFrame(tables)
        else:
            df = pd.DataFrame(tables.get("tables", []))

        # Отображаем таблицы с кнопками для просмотра
        if not df.empty:
            # Определяем, как называется колонка с именами таблиц
            if 'tablename' in df.columns:
                table_column = 'tablename'
            elif 'table_name' in df.columns:
                table_column = 'table_name'
            elif 'name' in df.columns:
                table_column = 'name'
            else:
                # Берем первую колонку
                table_column = df.columns[0]

            # Создаём колонку с кнопками
            cols = st.columns([3, 1])
            with cols[0]:
                st.write("**Table Name**")
            with cols[1]:
                st.write("**Action**")

            for idx, row in df.iterrows():
                table_name = row[table_column]
                cols = st.columns([3, 1])
                with cols[0]:
                    st.write(f"📊 {table_name}")
                with cols[1]:
                    if st.button(f"View", key=f"btn_{table_name}", width='stretch'):
                        st.session_state.selected_table = table_name

            # Показываем содержимое выбранной таблицы
            if st.session_state.selected_table:
                st.divider()
                st.subheader(f"Table: {st.session_state.selected_table}")

                # Параметр limit
                limit = st.slider(
                    "Rows to display",
                    min_value=10,
                    max_value=500,
                    value=100,
                    step=10,
                    key="limit_slider"
                )

                # Получаем данные таблицы
                table_data = fetch(f"/postgres/table/{st.session_state.selected_table}?limit={limit}")

                if table_data and "data" in table_data:
                    if table_data["data"]:
                        df_data = pd.DataFrame(table_data["data"])
                        st.dataframe(df_data, width='stretch')
                        st.caption(f"Showing {len(df_data)} rows from table '{st.session_state.selected_table}'")
                    else:
                        st.info(f"Table '{st.session_state.selected_table}' is empty")
                else:
                    st.error(f"Failed to load data from '{st.session_state.selected_table}'")

                # Кнопка закрытия
                if st.button("Close table view", width='stretch', key="close_table"):
                    st.session_state.selected_table = None
                    st.rerun()
        else:
            st.info("No tables found")
    else:
        st.info("No tables or error")

# --- Users ---
elif page == "Users":
    st.header("User Management")

    # Поиск по логину
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("Search user by login", placeholder="Enter login...")
    with col2:
        st.write("")
        search_btn = st.button("Search", width='stretch')

    if search_query and search_btn:
        users = fetch("/postgres/users")
        if users and isinstance(users, dict) and "users" in users:
            found = [u for u in users["users"] if search_query.lower() in u.get("login", "").lower()]
            if found:
                df = pd.DataFrame(found)
                st.dataframe(df, width='stretch')
                st.success(f"Found {len(found)} user(s)")
            else:
                st.warning(f"User '{search_query}' not found")
        else:
            st.error("Failed to fetch users")

    # Все пользователи
    st.subheader("All users")
    if st.button("Show all users", width='stretch'):
        users = fetch("/postgres/users")
        if users and isinstance(users, dict) and "users" in users:
            df = pd.DataFrame(users["users"])
            st.dataframe(df, width='stretch')
            st.caption(f"Total: {len(df)} users")
        else:
            st.warning("No user data")

# --- Activity ---
elif page == "Activity":
    st.header("Database Activity")

    if st.button("Refresh", width='stretch'):
        st.rerun()

    # Активные процессы
    processes = fetch("/postgres/requests")
    if processes and "requests" in processes:
        st.metric("Active processes", len(processes['requests']))
        if processes['requests']:
            df = pd.DataFrame(processes['requests'])
            st.dataframe(df, width='stretch')
    else:
        st.info("No active processes or connection error")

    # Транзакции
    st.subheader("Transactions")
    transactions = fetch("/postgres/transactions")
    if transactions:
        if isinstance(transactions, list):
            df = pd.DataFrame(transactions)
        else:
            df = pd.DataFrame(transactions.get("transactions", []))
        st.dataframe(df, width='stretch')
        st.caption(f"Total: {len(df)} transactions")
    else:
        st.info("No transaction data")

# --- Footer ---
st.divider()
st.caption("Midnight Dashboard v0.1.0")

# --- AUTO-REFRESH (в самом конце) ---
if auto_refresh:
    time.sleep(5)
    st.rerun()