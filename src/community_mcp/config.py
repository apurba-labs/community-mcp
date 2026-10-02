from functools import lru_cache
from typing import Literal

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"

    data_provider: Literal["demo", "gotihub"] = "demo"
    gotihub_base_url: HttpUrl | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
