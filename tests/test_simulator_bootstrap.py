from unittest.mock import MagicMock, patch

import pytest

from community_mcp.config import get_settings
from community_mcp.simulator.bootstrap import create_app

ORGANIZATION_ID = "11111111-1111-4111-8111-111111111111"


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_bootstrap_requires_mcp_configuration(monkeypatch):
    monkeypatch.setenv("SIMULATOR_MCP_URL", "")
    monkeypatch.setenv("SIMULATOR_MCP_ACCESS_TOKEN", "")

    with pytest.raises(RuntimeError, match="SIMULATOR_MCP_URL"):
        create_app()


def test_bootstrap_creates_fastapi_app(monkeypatch):
    monkeypatch.setenv(
        "SIMULATOR_MCP_URL",
        "https://mcp.example.com/mcp",
    )
    monkeypatch.setenv(
        "SIMULATOR_MCP_ACCESS_TOKEN",
        "test-token",
    )

    monkeypatch.setenv(
        "SIMULATOR_INTERNAL_API_TOKEN",
        "test-alumni-service-token",
    )

    with (
        patch("community_mcp.simulator.bootstrap.BedrockReasoner") as reasoner_class,
        patch("community_mcp.simulator.bootstrap.CommunityMCPClient") as client_class,
    ):
        reasoner_class.return_value = MagicMock()
        client_class.return_value = MagicMock()

        app = create_app()

    assert app.title == "Community MCP Experience Simulator"

    client_class.assert_called_once_with(
        server_url="https://mcp.example.com/mcp",
        access_token="test-token",
    )


@pytest.mark.asyncio
async def test_bootstrap_configures_internal_authentication(monkeypatch):
    import httpx

    monkeypatch.setenv(
        "SIMULATOR_MCP_URL",
        "https://mcp.example.com/mcp",
    )
    monkeypatch.setenv(
        "SIMULATOR_MCP_ACCESS_TOKEN",
        "test-mcp-token",
    )
    monkeypatch.setenv(
        "SIMULATOR_INTERNAL_API_TOKEN",
        "test-alumni-service-token",
    )

    with (
        patch("community_mcp.simulator.bootstrap.BedrockReasoner"),
        patch("community_mcp.simulator.bootstrap.CommunityMCPClient"),
    ):
        app = create_app()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        missing = await client.post(
            "/simulator/api/internal/chat",
            json={
                "message": "Hello",
                "organization_id": ORGANIZATION_ID,
            },
        )

        invalid = await client.post(
            "/simulator/api/internal/chat",
            headers={"Authorization": "Bearer incorrect"},
            json={
                "message": "Hello",
                "organization_id": ORGANIZATION_ID,
            },
        )
    assert missing.status_code == 401
    assert invalid.status_code == 401
