from community_mcp.config import Settings
from community_mcp.providers.assistance import AssistanceContextProvider
from community_mcp.providers.credentials import AccessTokenProvider
from community_mcp.providers.demo_assistance import DemoAssistanceProvider
from community_mcp.providers.gotihub_assistance import (
    GotiHubAssistanceProvider,
)


def create_assistance_provider(
    settings: Settings,
    *,
    credential_provider: AccessTokenProvider | None = None,
) -> AssistanceContextProvider:
    if settings.data_provider == "demo":
        return DemoAssistanceProvider()

    if settings.gotihub_base_url is None:
        raise ValueError("GOTIHUB_BASE_URL is required when DATA_PROVIDER=gotihub")

    if not settings.gotihub_organization_slug or not settings.gotihub_service_token:
        raise ValueError(
            "GOTIHUB_ORGANIZATION_SLUG and GOTIHUB_SERVICE_TOKEN "
            "are required when DATA_PROVIDER=gotihub"
        )

    return GotiHubAssistanceProvider(
        str(settings.gotihub_base_url),
        credential_provider,
        organization_slug=settings.gotihub_organization_slug,
        service_token=settings.gotihub_service_token,
    )
