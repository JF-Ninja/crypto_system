from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

env_path = Path(__file__).resolve().parent.parent.parent / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=env_path, env_file_encoding="utf-8", extra="ignore")

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



class JWTConfig(Settings):
    model_config = SettingsConfigDict(env_prefix="jwt_")
    private_key_path: str
    public_key_path: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int



class RedisConfig(Settings):
    model_config = SettingsConfigDict(env_prefix="redis_")
    host: str
    port: int
    password: str


db_config = DBConfig()
jwt_config = JWTConfig()
redis_config = RedisConfig()