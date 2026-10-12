import pytest

from community_mcp.config import Settings
from community_mcp.providers.assistance_factory import (
    create_assistance_provider,
)
from community_mcp.providers.gotihub_assistance import (
    GotiHubAssistanceProvider,
)


def test_create_gotihub_assistance_provider() -> None:
    provider = create_assistance_provider(
        Settings(
            _env_file=None,
            data_provider="gotihub",
            gotihub_base_url="https://community.example.org",
            gotihub_organization_slug="test-school",
            gotihub_service_token="synthetic-test-token",
        )
    )

    assert isinstance(provider, GotiHubAssistanceProvider)


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


@pytest.mark.parametrize(
    ("organization_slug", "service_token"),
    [
        (None, "synthetic-test-token"),
        ("test-school", None),
        ("test-school", ""),
    ],
)
def test_assistance_factory_rejects_missing_service_credentials(
    organization_slug: str | None,
    service_token: str | None,
) -> None:
    with pytest.raises(ValueError, match="GOTIHUB_ORGANIZATION_SLUG"):
        create_assistance_provider(
            Settings(
                _env_file=None,
                data_provider="gotihub",
                gotihub_base_url="https://community.example.org",
                gotihub_organization_slug=organization_slug,
                gotihub_service_token=service_token,
            )
        )
