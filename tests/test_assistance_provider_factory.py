import pytest

from community_mcp.config import Settings
from community_mcp.providers.assistance_factory import (
    create_assistance_provider,
)
from community_mcp.providers.demo_assistance import DemoAssistanceProvider
from community_mcp.providers.gotihub_assistance import (
    GotiHubAssistanceProvider,
)


def test_create_demo_assistance_provider() -> None:
    provider = create_assistance_provider(
        Settings(
            _env_file=None,
            data_provider="demo",
        )
    )

    assert isinstance(provider, DemoAssistanceProvider)


def test_gotihub_assistance_requires_base_url() -> None:
    settings = Settings(
        _env_file=None,
        data_provider="gotihub",
        gotihub_base_url=None,
    )

    with pytest.raises(
        ValueError,
        match="GOTIHUB_BASE_URL",
    ):
        create_assistance_provider(settings)


def test_create_gotihub_assistance_provider() -> None:
    provider = create_assistance_provider(
        Settings(
            _env_file=None,
            data_provider="gotihub",
            gotihub_base_url="https://community.example.org",
        )
    )

    assert isinstance(provider, GotiHubAssistanceProvider)