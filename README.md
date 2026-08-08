# Midnight API - Database Statistics Collector

Приложение для сбора и отображения статистики по базам данных: PostgreSQL, Redis, Memcached, MongoDB.

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

#### MongoDB
- `MONGO_HOST` - хост MongoDB (по умолчанию: localhost)
- `MONGO_PORT` - порт MongoDB (по умолчанию: 27017)
- `MONGO_USER` - пользователь (опционально)
- `MONGO_PASSWORD` - пароль (опционально)
- `MONGO_DB` - имя базы данных (по умолчанию: admin)

## Запуск приложения

```bash
# Для разработки с авто-перезагрузкой
uv run dev

# Для продакшена
uv run start
```

## Веб-дашборд

После запуска откройте в браузере `http://localhost:8000` — встроенный
дашборд в реальном времени показывает статус и метрики всех БД
(PostgreSQL, Redis, Memcached, MongoDB).

Данные стримятся по WebSocket `ws://localhost:8000/ws/stats`:
каждые 3 секунды сервер отправляет JSON со статистикой всех баз
параллельно. При разрыве соединения дашборд переподключается
автоматически.

## Подключения к БД

Каждое подключение — это независимая запись в реестре. Добавлять
и удалять подключения можно через веб-дашборд («Добавить БД») или
через REST API. Записи персистятся в файл `connections.json`
(в корне проекта, в git не попадает). При старте реестр
засевается подключениями из переменных окружения (см. ниже).

Если файла `connections.json` нет — при первом запуске будут
созданы 4 подключения по умолчанию (localhost для каждого типа БД).

### API подключений

- `GET /api/v1/connections/` — список всех подключений (пароль никогда не возвращается)
- `POST /api/v1/connections/` — создать подключение
- `DELETE /api/v1/connections/{id}` — удалить подключение
- `GET /api/v1/connections/{id}/test` — проверка доступности

Пример создания:

```bash
curl -X POST http://localhost:8000/api/v1/connections/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Prod PG","type":"postgres","host":"localhost","port":5432,"user":"postgres","password":"secret","database":"postgres"}'
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

### MongoDB
- `GET /api/v1/mongo/` - основная страница
- `GET /api/v1/mongo/ping` - проверка доступности
- `GET /api/v1/mongo/config` - текущая конфигурация
- `GET /api/v1/mongo/info` - полная статистика MongoDB
- `GET /api/v1/mongo/databases` - список баз данных MongoDB
- `GET /api/v1/mongo/stats` - статистика базы данных MongoDB

### Подключения
- `GET /api/v1/connections/` - список подключений
- `POST /api/v1/connections/` - создать подключение
- `DELETE /api/v1/connections/{id}` - удалить подключение
- `GET /api/v1/connections/{id}/test` - тест подключения

## Документация API

После запуска приложения документация доступна по адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Структура проекта

```
src/
├── api/
│   └── v1/
│       ├── postgres_routes.py      # Роуты PostgreSQL
│       ├── cache_routes.py         # Роуты Redis и Memcached
│       ├── mongo_routes.py         # Роуты MongoDB
│       └── connections_routes.py   # CRUD подключений
├── core/
│   ├── config.py                   # Конфигурация env (seed подключений)
│   ├── registry.py                 # Реестр подключений (JSON-персистенция)
│   ├── connection_manager.py       # Жизненный цикл клиентов по каждому подключению
│   ├── database.py                 # Подключение к PostgreSQL
│   ├── redis_db.py                 # Подключение к Redis
│   ├── memcache_db.py              # Подключение к Memcached
│   └── mongo_db.py                 # Подключение к MongoDB
├── repositories/
│   ├── check_postgres.py           # Функции для PostgreSQL
│   ├── check_cache_dbs.py          # Функции для Redis и Memcached
│   └── check_mongo.py              # Функции для MongoDB
├── services/
│   └── stats_collector.py          # Сбор статистики по всем подключениям для WS-дашборда
├── templates/
│   └── index.html                  # Веб-дашборд мониторинга (управление подключениями)
└── main.py                         # Точка входа приложения (+ /ws/stats)
```

## Пример использования

1. Запустите приложение:
```bash
uv run dev
```

2. Откройте браузер и перейдите на http://localhost:8000 — там веб-дашборд мониторинга

3. Добавьте подключения через кнопку «Добавить БД» на дашборде либо через
   переменные окружения в `.env` файле (они засеются при старте)

4. Приложение автоматически соберет статистику и отобразит её через API и дашборд
