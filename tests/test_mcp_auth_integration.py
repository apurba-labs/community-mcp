import json
import time

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from community_mcp.config import Settings
from community_mcp.providers.demo import DemoProvider
from community_mcp.server import create_mcp_server

ISSUER = "https://auth.example.test"
AUDIENCE = "https://mcp.example.test/mcp"
JWKS_URL = f"{ISSUER}/.well-known/jwks.json"


@pytest.mark.asyncio
async def test_real_signed_jwt_through_mcp_http(monkeypatch):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    public_jwk = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    public_jwk.update({"kid": "test-key-1", "use": "sig", "alg": "RS256"})

    jwks = {"keys": [public_jwk]}

    settings = Settings(
        app_env="development",
        data_provider="demo",
        mcp_capability_mode="public",
        mcp_auth_enabled=True,
        mcp_auth_issuer_url=ISSUER,
        mcp_auth_audience=AUDIENCE,
        mcp_auth_jwks_url=JWKS_URL,
        mcp_auth_required_scope="community.read",
    )

    monkeypatch.setattr(
        "community_mcp.server.get_settings",
        lambda: settings,
    )

    # Mock JWKS retrieval only; the real verifier performs signature validation.
    monkeypatch.setattr(
        "jwt.jwks_client.PyJWKClient.fetch_data",
        lambda self: jwks,
    )

    server = create_mcp_server(
        DemoProvider(),
        capability_mode="public",
    )

    app = server.streamable_http_app(
        json_response=True,
        stateless_http=True,
        host="127.0.0.1",
    )

    now = int(time.time())

    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + 3600,
        "client_id": "integration-test-client",
        "sub": "test-user",
        "scope": "community.read",
    }

    token = jwt.encode(
        claims,
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key-1"},
    )

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {
                "name": "integration-test",
                "version": "1.0",
            },
        },
    }

    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://127.0.0.1:8000",
        ) as client:
            response = await client.post(
                "/mcp",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            )

    assert response.status_code == 200, response.text
    assert response.json()["result"]["serverInfo"]["name"] == "Community MCP"
