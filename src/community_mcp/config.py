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
    gotihub_organization_slug: str | None = None
    gotihub_service_token: str | None = None
    gotihub_organization_id: str | None = None

    # Simulator
    simulator_mcp_url: str | None = None
    simulator_mcp_access_token: str | None = None
    simulator_mcp_token_file: str | None = None
    simulator_internal_api_token: str | None = None
    simulator_usage_db_path: str = "data/simulator_usage.sqlite3"

    reasoning_provider: Literal["deterministic", "bedrock"] = "deterministic"

    aws_profile: str | None = None
    bedrock_region: str = "us-east-1"
    bedrock_model_id: str = "amazon.nova-micro-v1:0"

    demo_ledger_enabled: bool = False
    demo_ledger_path: str = ".local/demo-assistance.sqlite3"

    # MCP server
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8000

    mcp_capability_mode: Literal["public", "demo"] = "public"

    mcp_auth_enabled: bool = False
    mcp_auth_issuer_url: OptionalHttpUrl = None
    mcp_auth_audience: str | None = None
    mcp_auth_jwks_url: OptionalHttpUrl = None
    mcp_auth_required_scope: str = "community.read"

    mcp_allowed_hosts: str = "127.0.0.1:8000,localhost:8000"
    mcp_allowed_origins: str = "http://127.0.0.1:8000,http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
