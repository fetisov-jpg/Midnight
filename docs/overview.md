# Обзор проекта

## Назначение

**Midnight** — асинхронный HTTP-API для сбора и выдачи операционной статистики
по трём типам хранилищ:

- **PostgreSQL** — версия, активные сессии, таблицы/индексы/представления, пользователи и т.д.
- **Redis** — `INFO`, размер БД, потребление памяти, uptime.
- **Memcached** — `stats`, ключи, соединения, использование памяти.

Целевая аудитория — разработчики и SRE, которым нужен быстрый «глазок» в
работающие инстансы без захода в psql/redis-cli напрямую.

## Стек

| Слой | Технология |
|---|---|
| HTTP-фреймворк | [FastAPI](https://fastapi.tiangolo.com/) 0.139 |
| ASGI-сервер | [Uvicorn](https://www.uvicorn.org/) |
| Драйвер PostgreSQL | [asyncpg](https://magicstack.github.io/asyncpg/) (пул 1–5) |
| Драйвер Redis | [redis-py asyncio](https://redis.readthedocs.io/) (`redis.asyncio`) |
| Драйвер Memcached | [aiomcache](https://aiomcache.readthedocs.io/) |
| Миграции | [Alembic](https://alembic.sqlalchemy.org/) (подключён, миграций нет) |
| Python | ≥ 3.13 |
| Управление зависимостями | [uv](https://github.com/astral-sh/uv) |

## Верхнеуровневая архитектура

```puml
@startuml
skinparam componentStyle rectangle
skinparam defaultTextAlignment center

actor "Клиент\n(curl / браузер)" as Client

rectangle "Midnight API\n(FastAPI, uvicorn :8000)" {
  ["/api/v1/postgres/*\n(PostgreSQL router)"] as PG
  ["/api/v1/redis/*\n(Redis router)"] as RD
  ["/api/v1/memcache/*\n(Memcached router)"] as MC

  package "core" {
    [database.py\nasyncpg.Pool] as DBCore
    [redis_db.py\naioredis client] as RDCore
    [memcache_db.py\naiomcache client] as MCCore
    [config.py\nPostgres/Redis/Memcache configs] as Cfg
  }

  package "repositories" {
    [check_postgres.py\nSELECT-запросы к pg_*, pg_stat_*] as PGRepo
    [check_cache_dbs.py\nINFO / stats"] as CacheRepo
  }
}

database "PostgreSQL" as PGSrv
database "Redis" as RDSrv
database "Memcached" as MCSrv

Client --> PG : HTTP GET
Client --> RD : HTTP GET
Client --> MC : HTTP GET

PG --> PGRepo
RD --> CacheRepo
MC --> CacheRepo

PGRepo --> DBCore : acquire connection
CacheRepo --> RDCore : INFO / DBSIZE
CacheRepo --> MCCore : stats()

DBCore  --> PGSrv : asyncpg over TCP 5432
RDCore  --> RDSrv : RESP over TCP 6379
MCCore  --> MCSrv : text protocol over TCP 11211

Cfg --> DBCore : env-driven
Cfg --> RDCore : env-driven
Cfg --> MCCore : env-driven
@enduml
```

## Структура каталогов

```
Midnight/
├── alembic.ini                       # Конфиг Alembic (миграций пока нет)
├── pyproject.toml                    # uv-проект: зависимости + скрипты
├── src/
│   ├── .env                          # Локальные переменные окружения (не в git)
│   ├── main.py                       # FastAPI app, lifespan, middleware
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py           # Аггрегирующий router
│   │       ├── postgres_routes.py    # /postgres/*
│   │       └── cache_routes.py       # /redis/* и /memcache/*
│   ├── core/
│   │   ├── config.py                 # Датаклассы конфигов + чтение .env
│   │   ├── database.py               # Пул PostgreSQL (asyncpg)
│   │   ├── redis_db.py               # Клиент Redis (redis.asyncio)
│   │   └── memcache_db.py            # Клиент Memcached (aiomcache)
│   ├── repositories/
│   │   ├── check_postgres.py         # SELECT-функции к системным каталогам PG
│   │   └── check_cache_dbs.py        # Сборщики статистики Redis/Memcached
│   ├── models/                       # Заготовки моделей (User, Model) — не используются API
│   ├── services/                     # Заготовка слоя сервисов — пустая
│   ├── mappers/                      # Заготовка слоя мапперов — пустая
│   └── utills/                       # Вспомогательное (пустое содержимое)
├── migrations/                       # Alembic env.py + шаблон
├── tests/                            # Заготовка (пустая)
└── docs/                             # ← эта документация
```

## Запуск

```bash
# development с авто-перезагрузкой
uv run dev

# production
uv run start
```

После запуска:

- Корневой `GET /` отдаёт карту эндпоинтов (см. [api.md](api.md)).
- Swagger UI: `http://localhost:8000/docs`.
- ReDoc: `http://localhost:8000/redoc`.

## Переменные окружения

Полный список — в [api.md § Конфигурация](api.md#конфигурация).
