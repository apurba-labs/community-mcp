from unittest.mock import MagicMock, patch

import pytest

from community_mcp.simulator.bootstrap import create_app


def test_bootstrap_requires_mcp_configuration(monkeypatch):
    monkeypatch.delenv("SIMULATOR_MCP_URL", raising=False)
    monkeypatch.delenv("SIMULATOR_MCP_ACCESS_TOKEN", raising=False)

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
