"""Opt-in integration test: real Bedrock inference + authenticated local MCP."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from mcp.server.auth.provider import AccessToken
from test_simulator_mcp_integration import (
    running_mcp_server,
)

from community_mcp.agent.bedrock import BedrockReasoner
from community_mcp.agent.schemas import SupportedLocale
from community_mcp.config import Settings
from community_mcp.providers.demo import DemoProvider
from community_mcp.server import create_mcp_server
from community_mcp.simulator.agent import SimulatorAgent
from community_mcp.simulator.mcp_client import CommunityMCPClient

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        os.environ.get("RUN_LIVE_BEDROCK_TESTS") != "1",
        reason="Requires explicit opt-in and AWS Bedrock access.",
    ),
]


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


async def test_real_bedrock_reasoning_with_authenticated_mcp(
    authenticated_mcp_app,
):
    reasoner = BedrockReasoner(
        profile_name=os.environ.get("AWS_PROFILE"),
        region_name="us-east-1",
        model_id="amazon.nova-micro-v1:0",
    )

    async with running_mcp_server(authenticated_mcp_app) as server_url:
        mcp_client = CommunityMCPClient(
            server_url=server_url,
            access_token="valid-test-token",
        )

        agent = SimulatorAgent(
            mcp_client=mcp_client,
            reasoner=reasoner,
        )

        session_id = str(uuid4())

        first = await agent.handle(
            message="When is the centenary celebration?",
            locale=SupportedLocale.EN,
            session_id=session_id,
        )

        second = await agent.handle(
            message="Can I register for the centenary celebration?",
            locale=SupportedLocale.EN,
            session_id=session_id,
        )

        bangla = await agent.handle(
            message="শতবর্ষ অনুষ্ঠান কবে হবে?",
            locale=SupportedLocale.BN,
            session_id=session_id,
        )

    assert first["intent"] == "EVENT_CONTEXT"
    assert first["tool"] == "get_event_context"
    assert first["event"]["slug"] == "centenary-celebration"

    # The local demo fixture has a published date and registration enabled.
    assert first["event"]["starts_at"] is not None
    assert first["event"]["registration_enabled"] is True

    assert "The event starts on" in first["message"]
    assert "currently enabled" in second["message"]

    assert bangla["intent"] == "EVENT_CONTEXT"
    assert bangla["tool"] == "get_event_context"
    assert "অনুষ্ঠান শুরু হবে" in bangla["message"]
