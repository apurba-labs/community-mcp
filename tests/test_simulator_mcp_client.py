from __future__ import annotations

from unittest.mock import patch

import pytest

from community_mcp.simulator.mcp_client import (
    CommunityMCPClient,
    CommunityMCPClientError,
)


def test_rejects_insecure_remote_endpoint() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        CommunityMCPClient(
            server_url="http://example.com/mcp",
            access_token="test-token",
        )


def test_requires_access_token() -> None:
    with pytest.raises(ValueError, match="access token"):
        CommunityMCPClient(
            server_url="https://example.com/mcp",
            access_token="",
        )


@pytest.mark.asyncio
async def test_rejects_non_public_tool() -> None:
    client = CommunityMCPClient(
        server_url="https://example.com/mcp",
        access_token="test-token",
    )

    with pytest.raises(ValueError, match="not permitted"):
        await client.call_tool(
            "confirm_assistance_response",
            {},
        )


@pytest.mark.asyncio
async def test_transport_failure_is_safe() -> None:
    client = CommunityMCPClient(
        server_url="https://example.com/mcp",
        access_token="test-token",
    )

    with patch(
        "community_mcp.simulator.mcp_client.streamable_http_client",
        side_effect=RuntimeError("Sensitive internal connection details"),
    ):
        with pytest.raises(
            CommunityMCPClientError,
            match="Unable to complete",
        ) as exc_info:
            await client.list_tools()

    assert "Sensitive internal connection details" not in str(exc_info.value)
