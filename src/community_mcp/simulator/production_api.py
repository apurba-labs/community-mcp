"""Production-only authenticated Alumni assistant API."""

from __future__ import annotations

from uuid import UUID

from community_mcp.config import get_settings
from community_mcp.providers.gotihub import GotiHubProvider
from community_mcp.simulator.alumni_agent import AlumniAgent
from community_mcp.simulator.api import create_simulator_app
from community_mcp.usage.store import SQLiteUsageStore, UsageBudget


def create_app():
    settings = get_settings()

    if settings.app_env != "production":
        raise RuntimeError("Alumni production API requires APP_ENV=production.")

    if not settings.simulator_internal_api_token:
        raise RuntimeError("SIMULATOR_INTERNAL_API_TOKEN is required.")

    if not settings.gotihub_organization_id:
        raise RuntimeError("GOTIHUB_ORGANIZATION_ID is required.")

    UUID(settings.gotihub_organization_id)

    if not all(
        (
            settings.gotihub_base_url,
            settings.gotihub_organization_slug,
            settings.gotihub_service_token,
        )
    ):
        raise RuntimeError("GotiHub integration configuration is incomplete.")

    provider = GotiHubProvider(
        base_url=str(settings.gotihub_base_url),
        organization_slug=settings.gotihub_organization_slug,
        service_token=settings.gotihub_service_token,
    )

    agent = AlumniAgent(provider=provider)

    usage_store = SQLiteUsageStore(settings.simulator_usage_db_path)

    alumni_budget = UsageBudget(
        daily_requests=200,
        concurrent_requests=3,
        daily_tokens=100_000,
    )

    return create_simulator_app(
        agent_factory=lambda: agent,
        internal_agent_factory=lambda: agent,
        internal_organization_id=settings.gotihub_organization_id,
        internal_api_token=settings.simulator_internal_api_token,
        usage_store=usage_store,
        alumni_budget=alumni_budget,
        internal_only=True,
    )


app = create_app()
