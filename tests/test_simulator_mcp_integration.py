from __future__ import annotations

import asyncio
import socket
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
import uvicorn
from mcp.server.auth.provider import AccessToken

from community_mcp.config import Settings
from community_mcp.providers.demo import DemoProvider
from community_mcp.server import create_mcp_server
from community_mcp.simulator.mcp_client import CommunityMCPClient, CommunityMCPClientError


@asynccontextmanager
async def running_mcp_server(app):
    """Run the actual MCP ASGI app on a local ephemeral port."""

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="error",
        lifespan="on",
    )

    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())

    try:
        for _ in range(100):
            if server.started:
                break

            if task.done():
                raise RuntimeError("Local MCP server exited unexpectedly.")

            await asyncio.sleep(0.05)
        else:
            raise RuntimeError("Local MCP server did not start.")

        yield f"http://127.0.0.1:{port}/mcp"

    finally:
        server.should_exit = True
        await asyncio.wait_for(task, timeout=10)


@pytest.fixture
def authenticated_mcp_app(monkeypatch):
    settings = Settings(
        app_env="development",
        data_provider="demo",
        mcp_capability_mode="public",
        mcp_auth_enabled=True,
        mcp_auth_issuer_url="https://auth.example.test",
        mcp_auth_audience="https://mcp.example.test/mcp",
        mcp_auth_jwks_url="https://auth.example.test/jwks.json",
        mcp_auth_required_scope="community.read",
    )

    monkeypatch.setattr(
        "community_mcp.server.get_settings",
        lambda: settings,
    )

    server = create_mcp_server(
        DemoProvider(),
        capability_mode="public",
    )

    async def verify_token(token):
        if token != "valid-test-token":
            return None

        return AccessToken(
            token=token,
            client_id="simulator-integration-test",
            scopes=["community.read"],
            resource="https://mcp.example.test/mcp",
        )

    monkeypatch.setattr(
        server._token_verifier,
        "verify_token",
        AsyncMock(side_effect=verify_token),
    )

    return server.streamable_http_app(
        json_response=True,
        stateless_http=True,
        host="127.0.0.1",
    )


@pytest.mark.asyncio
async def test_simulator_client_discovers_and_calls_real_mcp_tools(
    authenticated_mcp_app,
):
    async with running_mcp_server(authenticated_mcp_app) as server_url:
        client = CommunityMCPClient(
            server_url=server_url,
            access_token="valid-test-token",
        )

        tools = await client.list_tools()

        assert {tool.name for tool in tools} == {
            "get_event_context",
            "get_assistance_context",
        }

        result = await client.call_tool(
            "get_event_context",
            {"event_slug": "centenary-celebration"},
        )

    assert result.is_error is False
    assert result.structured_content is not None

    event = result.structured_content

    assert event["slug"] == "centenary-celebration"
    assert event["event_type"] == "CENTENARY"
    assert len(event["program"]) == 3


@pytest.mark.asyncio
async def test_simulator_client_rejects_invalid_token(
    authenticated_mcp_app,
):
    async with running_mcp_server(authenticated_mcp_app) as server_url:
        client = CommunityMCPClient(
            server_url=server_url,
            access_token="invalid-test-token",
        )

        with pytest.raises(
            CommunityMCPClientError,
            match="Unable to complete",
        ) as exc_info:
            await client.list_tools()
        assert "Sensitive internal connection details" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_simulator_client_calls_real_assistance_tool(
    authenticated_mcp_app,
):
    async with running_mcp_server(authenticated_mcp_app) as server_url:
        client = CommunityMCPClient(
            server_url=server_url,
            access_token="valid-test-token",
        )

        result = await client.call_tool(
            "get_assistance_context",
            {"public_reference": "HELP-2026-001"},
        )

    assert result.is_error is False
    assert result.structured_content is not None

    assistance = result.structured_content

    assert assistance["public_reference"] == "HELP-2026-001"
    assert assistance["assistance_type"] == "BLOOD"
    assert assistance["status"] == "ACTIVE"
    assert assistance["verified"] is True
    assert assistance["approved"] is True


@pytest.mark.asyncio
async def test_simulator_client_handles_missing_assistance_reference(
    authenticated_mcp_app,
):
    async with running_mcp_server(authenticated_mcp_app) as server_url:
        client = CommunityMCPClient(
            server_url=server_url,
            access_token="valid-test-token",
        )

        with pytest.raises(CommunityMCPClientError):
            await client.call_tool(
                "get_assistance_context",
                {"public_reference": "HELP-2026-999"},
            )
