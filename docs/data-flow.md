# Потоки данных

Ниже — sequence-диаграммы для трёх ключевых сценариев: чтение метрик
PostgreSQL, Redis и Memcached. Все эндпоинты идемпотентны, никаких
побочных эффектов не вызывают.

## Общий путь HTTP-запроса

```puml
@startuml
actor Client
participant "uvicorn" as UV
participant "FastAPI\napp" as App
participant "Router\n(/api/v1/...)" as R
participant "Repository\n(repositories/...)" as Repo
participant "core/*_db.py" as Core
participant "DB / Cache\n(внешний сервер)" as DB

Client -> UV : HTTP GET /api/v1/postgres/tables
UV -> App : ASGI scope + receive
App -> R : match route
R -> Repo : await get_tables()
Repo -> Core : await get_pg_pool()\n+ pool.acquire()
Core -> DB : TCP 5432\nSELECT tablename FROM pg_tables ...
DB --> Core : rows
Core --> Repo : asyncpg.Record
Repo --> R : list[dict]
R --> App : JSONResponse
App --> UV : HTTP 200
UV --> Client : body
@enduml
```

## PostgreSQL: список таблиц

```puml
@startuml
actor Client
participant "FastAPI" as App
participant "postgres_routes.get_tables_pg" as Route
participant "check_postgres.get_tables" as Repo
participant "database.get_pg_pool" as Core
participant "PostgreSQL" as PG

Client -> App : GET /api/v1/postgres/tables
App -> Route : handler
Route -> Repo : await get_tables()
Repo -> Core : await get_pg_pool()
Core --> Repo : asyncpg.Pool
Repo -> PG : SELECT tablename FROM pg_tables WHERE schemaname='public'
PG --> Repo : rows
Repo --> Route : list[dict]
Route --> App : {"status":"ok"} || rows
App --> Client : 200 JSON
@enduml
```

## Redis: `INFO` + `DBSIZE`

```puml
@startuml
actor Client
participant "FastAPI" as App
participant "cache_routes.get_redis_info" as Route
participant "check_cache_dbs.check_redis_info" as Repo
participant "redis_db.get_redis_conn" as Core
participant "Redis" as RDS

Client -> App : GET /api/v1/redis/info
App -> Route : handler
Route -> Repo : await check_redis_info()
Repo -> Core : await get_redis_conn()
Core --> Repo : aioredis.Redis
Repo -> RDS : INFO
RDS --> Repo : dict (raw INFO)
Repo -> RDS : DBSIZE
RDS --> Repo : int (key count)
Repo --> Route : {status, config, info, db_size}
Route --> App : JSON
App --> Client : 200 JSON
@enduml
```

## Memcached: `stats`

```puml
@startuml
actor Client
participant "FastAPI" as App
participant "cache_routes.get_memcache_stats" as Route
participant "check_cache_dbs.check_memcache_stats" as Repo
participant "memcache_db.get_memcache_conn" as Core
participant "Memcached" as MC

Client -> App : GET /api/v1/memcache/stats
App -> Route : handler
Route -> Repo : await check_memcache_stats()
Repo -> Core : await get_memcache_conn()
Core --> Repo : aiomcache.Client
Repo -> MC : stats
MC --> Repo : dict[server_key, stats_bytes]
Repo -> Repo : выбрать первый сервер\nи декодировать поля
Repo --> Route : {status, config, stats}
Route --> App : JSON
App --> Client : 200 JSON
@enduml
```

## Жизненный цикл соединений

```puml
@startuml
participant "FastAPI app" as App
participant "database.get_pg_pool" as PG
participant "redis_db.get_redis_conn" as RD
participant "memcache_db.get_memcache_conn" as MC

note over App: Старт uvicorn
App -> PG : (lazy) первый запрос → create_pool()
App -> RD : (lazy) → aioredis.from_url()
App -> MC : (lazy) → aiomcache.Client()

note over App: ...
note over App: SIGTERM / shutdown
App -> PG : close_pg()
App -> RD : close_redis()
App -> MC : close_memcache()
@enduml
```

Все три клиента — module-level singletons, инициализируются при первом
обращении и закрываются на событии `shutdown`.
