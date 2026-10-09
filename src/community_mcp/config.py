from functools import lru_cache
from typing import Annotated, Literal

from pydantic import BeforeValidator, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


def empty_string_to_none(value: object) -> object:
    if isinstance(value, str) and not value.strip():
        return None
    return value


OptionalHttpUrl = Annotated[
    HttpUrl | None,
    BeforeValidator(empty_string_to_none),
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"

    data_provider: Literal["demo", "gotihub"] = "demo"
    gotihub_base_url: OptionalHttpUrl = None

    reasoning_provider: Literal["deterministic", "bedrock"] = "deterministic"

    aws_profile: str | None = None
    bedrock_region: str = "us-east-1"
    bedrock_model_id: str = "amazon.nova-micro-v1:0"

    demo_ledger_enabled: bool = False
    demo_ledger_path: str = ".local/demo-assistance.sqlite3"


@lru_cache
def get_settings() -> Settings:
    return Settings()
