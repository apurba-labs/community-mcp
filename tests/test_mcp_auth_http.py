from unittest.mock import AsyncMock

import httpx
import pytest
from mcp.server.auth.provider import AccessToken

from community_mcp.providers.demo import DemoProvider
from community_mcp.server import create_mcp_server


@pytest.fixture
def authenticated_app(monkeypatch):
    from community_mcp.config import Settings

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

    verifier = server._token_verifier

    async def verify_token(token):
        if token == "valid-token":
            return AccessToken(
                token=token,
                client_id="test-client",
                scopes=["community.read"],
                resource="https://mcp.example.test/mcp",
            )

        if token == "missing-scope":
            return AccessToken(
                token=token,
                client_id="test-client",
                scopes=[],
                resource="https://mcp.example.test/mcp",
            )

        return None

    monkeypatch.setattr(
        verifier,
        "verify_token",
        AsyncMock(side_effect=verify_token),
    )

    return server.streamable_http_app(
        json_response=True,
        stateless_http=True,
        host="127.0.0.1",
    )


@pytest.mark.asyncio
async def test_http_authentication(authenticated_app):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {
                "name": "auth-test",
                "version": "1.0",
            },
        },
    }

    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }

    async with authenticated_app.router.lifespan_context(authenticated_app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=authenticated_app),
            base_url="http://127.0.0.1:8000",
        ) as client:
            cases = [
                ("Anonymous", {}, 401),
                ("Invalid token", {"Authorization": "Bearer invalid"}, 401),
                ("Missing scope", {"Authorization": "Bearer missing-scope"}, 403),
                ("Valid token", {"Authorization": "Bearer valid-token"}, 200),
            ]

            for name, extra_headers, expected in cases:
                response = await client.post(
                    "/mcp",
                    json=payload,
                    headers={**headers, **extra_headers},
                )

                print(f"{name}: HTTP {response.status_code}")

                assert response.status_code == expected, (
                    f"{name}: expected {expected}, got {response.status_code}"
                )
