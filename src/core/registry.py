import json
import os
import uuid
from dataclasses import asdict, dataclass

from src.core.config import MemcacheConfig, MongoConfig, PostgresConfig, RedisConfig

CONNECTIONS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "connections.json"
)

CONNECTION_TYPES = ("postgres", "redis", "memcache", "mongo")

DEFAULT_PORTS = {
    "postgres": 5432,
    "redis": 6379,
    "memcache": 11211,
    "mongo": 27017,
}

DEFAULT_DATABASES = {
    "postgres": "postgres",
    "mongo": "admin",
}


@dataclass
class ConnectionConfig:
    id: str
    name: str
    type: str
    host: str
    port: int
    user: str | None = None
    password: str | None = None
    database: str | None = None
    description: str | None = None

    def to_dict(self, include_password: bool = False) -> dict:
        data = asdict(self)
        if not include_password:
            data.pop("password", None)
        return data


class ConnectionRegistry:
    """Хранит конфигурации подключений и персистит их в JSON-файл"""

    def __init__(self, path: str = CONNECTIONS_FILE):
        self._path = path
        self._connections: dict[str, ConnectionConfig] = {}

    def load(self) -> None:
        if os.path.exists(self._path):
            try:
                with open(self._path, encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    cfg = ConnectionConfig(**item)
                    self._connections[cfg.id] = cfg
                return
            except (OSError, ValueError, TypeError):
                pass
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        """На первом старте создаёт подключения из переменных окружения"""
        pg = PostgresConfig.from_env()
        pg_id = uuid.uuid4().hex
        self._connections[pg_id] = ConnectionConfig(
            id=pg_id,
            name="PostgreSQL",
            type="postgres",
            host=pg.host,
            port=pg.port,
            user=pg.user,
            password=pg.password,
            database=pg.database,
        )
        rd = RedisConfig.from_env()
        rd_id = uuid.uuid4().hex
        self._connections[rd_id] = ConnectionConfig(
            id=rd_id,
            name="Redis",
            type="redis",
            host=rd.host,
            port=rd.port,
            password=rd.password,
            database=str(rd.db),
        )
        mc = MemcacheConfig.from_env()
        mc_id = uuid.uuid4().hex
        self._connections[mc_id] = ConnectionConfig(
            id=mc_id,
            name="Memcached",
            type="memcache",
            host=mc.host,
            port=mc.port,
        )
        mo = MongoConfig.from_env()
        mo_id = uuid.uuid4().hex
        self._connections[mo_id] = ConnectionConfig(
            id=mo_id,
            name="MongoDB",
            type="mongo",
            host=mo.host,
            port=mo.port,
            user=mo.user,
            password=mo.password,
            database=mo.database,
        )
        self.save()

    def save(self) -> None:
        data = [asdict(c) for c in self._connections.values()]
        tmp = self._path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self._path)

    def add(self, config: ConnectionConfig) -> ConnectionConfig:
        self._connections[config.id] = config
        self.save()
        return config

    def remove(self, connection_id: str) -> bool:
        if connection_id in self._connections:
            del self._connections[connection_id]
            self.save()
            return True
        return False

    def get(self, connection_id: str) -> ConnectionConfig | None:
        return self._connections.get(connection_id)

    def list(self) -> list[ConnectionConfig]:
        return sorted(self._connections.values(), key=lambda c: (c.type, c.name))


_registry: ConnectionRegistry | None = None


def get_registry() -> ConnectionRegistry:
    global _registry
    if _registry is None:
        _registry = ConnectionRegistry()
        _registry.load()
    return _registry
