# API Reference

Все эндпоинты — `GET`, в формате JSON. Префикс: `/api/v1`.
Полный OpenAPI-схема доступна по `GET /openapi.json`, UI — по `/docs`.

## Конвенции ответов

- Успех: HTTP 200 + JSON-тело результата.
- Ошибка нижнего уровня (БД недоступна, таймаут): HTTP 200 + JSON
  `{"status": "error", "message": "<текст исключения>"}` —
  ошибки не пробрасываются как `HTTPException`, а глушатся в `try/except`
  на уровне роута. Это **by design**, чтобы дашборд мог отображать
  статус без необходимости парсить `4xx/5xx`.

## Корневой эндпоинт

### `GET /`

Веб-дашборд мониторинга (HTML). Данные стримятся через
`/ws/stats`.

## WebSocket: `/ws/stats`

Стрим статистики всех баз данных. Сервер отправляет JSON
каждые 3 секунды.

**Формат сообщения**

```json
{
  "postgresql": {"status": "connected", "metrics": {"version": "...", "active_connections": 5, "latency_ms": 12.3}},
  "redis": {"status": "connected", "metrics": {"version": "7.x.y", "uptime_seconds": 123, "used_memory_human": "1.2M", "connected_clients": 7, "db_size": 42, "latency_ms": 1.1}},
  "memcached": {"status": "connected", "metrics": {"uptime": 1000, "curr_items": 5, "curr_connections": 2, "get_hits": 100, "get_misses": 5, "latency_ms": 0.9}},
  "mongodb": {"status": "connected", "metrics": {"version": "8.x", "uptime_seconds": 100, "connections": 3, "latency_ms": 8.4}}
}
```

При недоступности БД секция имеет вид
`{"status": "error", "message": "<текст исключения>", "metrics": {"latency_ms": 0.0}}`.

---

## PostgreSQL — `/api/v1/postgres/*`

### `GET /api/v1/postgres/`

Заглушка-карта группы.

**Ответ 200:** `{"message": "PostgreSQL endpoints"}`

### `GET /api/v1/postgres/ping`

Проверка живости роутера. **Не** делает запрос в БД.

**Ответ 200:** `{"status": "pong"}`

### `GET /api/v1/postgres/config`

Текущая конфигурация подключения (из env, пароль скрыт).

**Ответ 200**

```json
{ "host": "localhost", "port": 5432, "user": "postgres", "database": "postgres" }
```

### `GET /api/v1/postgres/db-test`

Открывает соединение из пула, выполняет `SELECT 1`.

**Ответ 200 (успех):** `{"status": "ok", "message": "Database connected"}`
**Ответ 200 (ошибка):** `{"status": "error", "message": "..."}`

### `GET /api/v1/postgres/check-version`

Возвращает строку `SELECT version()` целиком.

**Ответ 200:** `{"version": "PostgreSQL 16.x ..."}`

### `GET /api/v1/postgres/requests`

Снимок `pg_stat_activity`.

**Ответ 200:** массив объектов (ключи зависят от версии PG).

### `GET /api/v1/postgres/users`

`SELECT usename, usesuper, usecreatedb, valuntil FROM pg_user;`

**Ответ 200:** массив объектов-пользователей.

### `GET /api/v1/postgres/tables`

`SELECT tablename FROM pg_tables WHERE schemaname = 'public';`

**Ответ 200:** `[{"tablename": "..."}, ...]`

### `GET /api/v1/postgres/databases`

`SELECT datname FROM pg_database;`

**Ответ 200:** `[{"datname": "..."}, ...]`

### `GET /api/v1/postgres/transactions`

Текущие запросы из `pg_stat_activity`, отсортированные по давности.

**Ответ 200:** массив объектов с `pid`, `usename`, `application_name`,
`client_addr`, `state`, `query`, `query_start`, `duration`.

### `GET /api/v1/postgres/indexes`

Все индексы схемы `public` + список колонок каждой таблицы
(через подзапрос в `information_schema.columns`).

**Ответ 200:** `{"indexes": [ ... ]}`

### `GET /api/v1/postgres/indexes/{table_name}`

Индексы конкретной таблицы.

**Параметры пути**

| Имя | Тип | Описание |
|---|---|---|
| `table_name` | string | Имя таблицы в схеме `public` |

**Ответ 200**

```json
{
  "table": "users",
  "indexes": [
    {"indexname": "users_pkey", "indexdef": "CREATE UNIQUE INDEX ..."}
  ]
}
```

**Ответ 200 (ошибка):** `{"error": "...", "table": "<name>"}`

### `GET /api/v1/postgres/extensions`

`SELECT * FROM pg_available_extensions;` — перечень **доступных**
(не установленных) расширений.

**Ответ 200:** `{"extensions": [ ... ]}`

### `GET /api/v1/postgres/views`

Представления схемы `public`.

**Ответ 200:** `{"views": [{"schemaname": "public", "viewname": "...", ...}]}`

### `GET /api/v1/postgres/materialized_views`

Материализованные представления.

**Ответ 200:** `{"materialized_views": [ ... ]}`

---

## Redis — `/api/v1/redis/*`

### `GET /api/v1/redis/`

Заглушка.

**Ответ 200:** `{"message": "Redis endpoints"}`

### `GET /api/v1/redis/ping`

Проверка живости роутера.

**Ответ 200:** `{"status": "pong"}`

### `GET /api/v1/redis/config`

Конфигурация подключения (без пароля).

**Ответ 200:** `{"host": "localhost", "port": 6379, "db": 0}`

### `GET /api/v1/redis/info`

Полный снимок метрик.

**Ответ 200 (успех)**

```json
{
  "status": "connected",
  "config": {"host": "localhost", "port": 6379, "db": 0},
  "info": {
    "redis_version": "7.x.y",
    "uptime_in_seconds": 12345,
    "connected_clients": 7,
    "used_memory_human": "1.23M",
    "total_connections_received": 100,
    "keyspace_hits": 900,
    "keyspace_misses": 50
  },
  "db_size": 42
}
```

**Ответ 200 (ошибка):** `{"status": "error", "message": "..."}`

---

## Memcached — `/api/v1/memcache/*`

### `GET /api/v1/memcache/`

Заглушка.

**Ответ 200:** `{"message": "Memcached endpoints"}`

### `GET /api/v1/memcache/ping`

Проверка живости роутера.

**Ответ 200:** `{"status": "pong"}`

### `GET /api/v1/memcache/config`

**Ответ 200:** `{"host": "localhost", "port": 11211}`

### `GET /api/v1/memcache/stats`

**Ответ 200 (успех)**

```json
{
  "status": "connected",
  "config": {"host": "localhost", "port": 11211},
  "stats": {
    "pid": 1234,
    "uptime": 100000,
    "curr_items": 5,
    "total_items": 20,
    "curr_connections": 2,
    "total_connections": 50,
    "bytes": 2048,
    "get_hits": 100,
    "get_misses": 5,
    "bytes_read": 8192,
    "bytes_written": 4096
  }
}
```

**Ответ 200 (ошибка):** `{"status": "error", "message": "..."}`

---

## Конфигурация

Все настройки — из переменных окружения (см. `src/.env`). Чтение
через `src/core/config.py::*.from_env()`.

| Переменная | Дефолт | Описание |
|---|---|---|
| `POSTGRES_HOST` | `localhost` | |
| `POSTGRES_PORT` | `5432` | |
| `POSTGRES_USER` | `postgres` | |
| `POSTGRES_PASSWORD` | `postgres` | |
| `POSTGRES_DB` | `postgres` | |
| `REDIS_HOST` | `localhost` | |
| `REDIS_PORT` | `6379` | |
| `REDIS_PASSWORD` | _нет_ | Если задано, попадает в `redis://:pass@host:port/db` |
| `REDIS_DB` | `0` | Номер логической БД |
| `MEMCACHE_HOST` | `localhost` | |
| `MEMCACHE_PORT` | `11211` | |
