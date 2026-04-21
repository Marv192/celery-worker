from pydantic import HttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CeleryWorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)
    redis_host: str = Field(default="redis_celery_worker")
    redis_port: int = Field(default=6379)
    api_key: str
    orders_service_url: HttpUrl = Field(default="http://mock-orders:8080/orders")
    cache_ttl: int = Field(default=3600)
    db_currency: str = Field(default="USD", pattern="^[A-Z]{3}$")


settings = CeleryWorkerSettings()
