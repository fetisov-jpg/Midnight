import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class PostgresConfig:
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "postgres"
    
    @property
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @classmethod
    def from_env(cls) -> "PostgresConfig":
        return cls(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            database=os.getenv("POSTGRES_DB", "postgres"),
        )


@dataclass
class RedisConfig:
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    
    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"
    
    @classmethod
    def from_env(cls) -> "RedisConfig":
        return cls(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),
            db=int(os.getenv("REDIS_DB", "0")),
        )


@dataclass
class MemcacheConfig:
    host: str = "localhost"
    port: int = 11211
    
    @property
    def server(self) -> str:
        return f"{self.host}:{self.port}"
    
    @classmethod
    def from_env(cls) -> "MemcacheConfig":
        return cls(
            host=os.getenv("MEMCACHE_HOST", "localhost"),
            port=int(os.getenv("MEMCACHE_PORT", "11211")),
        )


@dataclass
class DatabaseConfig:
    postgres: PostgresConfig
    redis: RedisConfig
    memcache: MemcacheConfig
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        return cls(
            postgres=PostgresConfig.from_env(),
            redis=RedisConfig.from_env(),
            memcache=MemcacheConfig.from_env(),
        )
