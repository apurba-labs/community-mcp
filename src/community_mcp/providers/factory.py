from community_mcp.config import Settings
from community_mcp.providers.base import CommunityDataProvider
from community_mcp.providers.demo import DemoProvider
from community_mcp.providers.gotihub import GotiHubProvider


def create_provider(settings: Settings) -> CommunityDataProvider:
    if settings.data_provider == "demo":
        return DemoProvider()

    if settings.gotihub_base_url is None:
        raise ValueError(
            "GOTIHUB_BASE_URL is required when DATA_PROVIDER=gotihub"
        )

    return GotiHubProvider(str(settings.gotihub_base_url))
