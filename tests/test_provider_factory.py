import pytest

from community_mcp.config import Settings
from community_mcp.providers.demo import DemoProvider
from community_mcp.providers.factory import create_provider
from community_mcp.providers.gotihub import GotiHubProvider


def test_factory_creates_demo_provider() -> None:
    provider = create_provider(Settings(data_provider="demo"))

    assert isinstance(provider, DemoProvider)


def test_factory_creates_gotihub_provider() -> None:
    provider = create_provider(
        Settings(
            _env_file=None,
            data_provider="gotihub",
            gotihub_base_url="https://community.example.org",
            gotihub_organization_slug="test-school",
            gotihub_service_token="synthetic-test-token",
        )
    )

    assert isinstance(provider, GotiHubProvider)


def test_factory_requires_gotihub_base_url() -> None:
    with pytest.raises(ValueError, match="GOTIHUB_BASE_URL"):
        create_provider(
            Settings(
                data_provider="gotihub",
                gotihub_base_url=None,
            )
        )


def test_settings_accepts_blank_optional_gotihub_base_url(
    monkeypatch,
) -> None:
    monkeypatch.setenv("GOTIHUB_BASE_URL", "")

    settings = Settings(_env_file=None)

    assert settings.gotihub_base_url is None


@pytest.mark.parametrize(
    ("organization_slug", "service_token"),
    [
        (None, "synthetic-test-token"),
        ("test-school", None),
        ("test-school", ""),
    ],
)
def test_gotihub_factory_rejects_missing_service_credentials(
    organization_slug: str | None,
    service_token: str | None,
) -> None:
    with pytest.raises(ValueError, match="GOTIHUB_ORGANIZATION_SLUG"):
        create_provider(
            Settings(
                _env_file=None,
                data_provider="gotihub",
                gotihub_base_url="https://community.example.org",
                gotihub_organization_slug=organization_slug,
                gotihub_service_token=service_token,
            )
        )
