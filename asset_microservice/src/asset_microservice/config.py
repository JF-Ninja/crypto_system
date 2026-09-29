from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

env_path = Path(__file__).resolve().parent.parent.parent / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=env_path, env_file_encoding="utf-8", extra="ignore")

class RedisConfig(Settings):
    model_config = SettingsConfigDict(env_prefix="redis_")
    host: str
    port: int
    password: str

class TickerConfig(Settings):
    model_config = SettingsConfigDict(env_prefix="ticker_")
    url: str

class RabbitMQConfig(Settings):
    model_config = SettingsConfigDict(env_prefix="rabbitmq_")
    url: str

redis_config = RedisConfig()
ticker_config = TickerConfig()
rabbitmq_config = RabbitMQConfig()