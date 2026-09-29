from pathlib import Path
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

env_part = Path(__file__).resolve().parent.parent.parent / ".env"
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=env_part, env_file_encoding="utf-8", extra="ignore")

class DBConfig(Settings):
    model_config = SettingsConfigDict(env_prefix="db_")
    host: str
    name: str
    port: int
    user: str
    password: str

    @computed_field
    def db_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

class RedisConfig(Settings):
    model_config = SettingsConfigDict(env_prefix="redis_")
    host: str
    port: int
    password: str


class RabbitMQConfig(Settings):
    model_config = SettingsConfigDict(env_prefix="rabbitmq_")
    url: str


class SMTPConfig(Settings):
    model_config = SettingsConfigDict(env_prefix="smtp_")
    login: str
    password: str


db_config =DBConfig()
redis_config = RedisConfig()
rabbitmq_config = RabbitMQConfig()
smtp_config = SMTPConfig()