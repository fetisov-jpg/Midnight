# Midnight API - Database Statistics Collector

Приложение для сбора и отображения статистики по базам данных: PostgreSQL, Redis, Memcached.

## Установка зависимостей

```bash
uv sync
```

## Настройка

Скопируйте файл `.env.example` в `.env` и настройте параметры подключения:

```bash
cp .env.example .env
```

### Переменные окружения

#### PostgreSQL
- `POSTGRES_HOST` - хост PostgreSQL (по умолчанию: localhost)
- `POSTGRES_PORT` - порт PostgreSQL (по умолчанию: 5432)
- `POSTGRES_USER` - пользователь (по умолчанию: postgres)
- `POSTGRES_PASSWORD` - пароль (по умолчанию: postgres)
- `POSTGRES_DB` - имя базы данных (по умолчанию: postgres)

#### Redis
- `REDIS_HOST` - хост Redis (по умолчанию: localhost)
- `REDIS_PORT` - порт Redis (по умолчанию: 6379)
- `REDIS_PASSWORD` - пароль Redis (опционально)
- `REDIS_DB` - номер базы данных (по умолчанию: 0)

#### Memcached
- `MEMCACHE_HOST` - хост Memcached (по умолчанию: localhost)
- `MEMCACHE_PORT` - порт Memcached (по умолчанию: 11211)

## Запуск приложения

```bash
# Для разработки с авто-перезагрузкой
uv run dev

# Для продакшена
uv run start
```

## API Endpoints

### PostgreSQL
- `GET /api/v1/postgres/` - основная страница
- `GET /api/v1/postgres/ping` - проверка доступности
- `GET /api/v1/postgres/config` - текущая конфигурация
- `GET /api/v1/postgres/db-test` - тест подключения
- `GET /api/v1/postgres/check-version` - версия PostgreSQL
- `GET /api/v1/postgres/requests` - активные запросы
- `GET /api/v1/postgres/users` - пользователи
- `GET /api/v1/postgres/tables` - таблицы
- `GET /api/v1/postgres/databases` - базы данных
- `GET /api/v1/postgres/transactions` - транзакции
- `GET /api/v1/postgres/indexes` - индексы схемы
- `GET /api/v1/postgres/indexes/{table_name}` - индексы таблицы
- `GET /api/v1/postgres/extensions` - расширения
- `GET /api/v1/postgres/views` - представления
- `GET /api/v1/postgres/materialized_views` - материализованные представления

### Redis
- `GET /api/v1/redis/` - основная страница
- `GET /api/v1/redis/ping` - проверка доступности
- `GET /api/v1/redis/config` - текущая конфигурация
- `GET /api/v1/redis/info` - полная статистика Redis

### Memcached
- `GET /api/v1/memcache/` - основная страница
- `GET /api/v1/memcache/ping` - проверка доступности
- `GET /api/v1/memcache/config` - текущая конфигурация
- `GET /api/v1/memcache/stats` - статистика Memcached

## Документация API

После запуска приложения документация доступна по адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Структура проекта

```
src/
├── api/
│   └── v1/
│       ├── postgres_routes.py    # Роуты PostgreSQL
│       └── cache_routes.py       # Роуты Redis и Memcached
├── core/
│   ├── config.py                 # Конфигурация всех БД
│   ├── database.py               # Подключение к PostgreSQL
│   ├── redis_db.py               # Подключение к Redis
│   └── memcache_db.py            # Подключение к Memcached
├── repositories/
│   ├── check_postgres.py         # Функции для PostgreSQL
│   └── check_cache_dbs.py        # Функции для Redis и Memcached
└── main.py                       # Точка входа приложения
```

## Пример использования

1. Запустите приложение:
```bash
uv run dev
```

2. Откройте браузер и перейдите на http://localhost:8000/docs

3. Укажите креды баз данных через переменные окружения в `.env` файле

4. Приложение автоматически соберет статистику и отобразит её через API
