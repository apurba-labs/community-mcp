from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from community_mcp.simulator.api import ChatRateLimiter, create_simulator_app


@pytest.fixture
def agent():
    mock = MagicMock()
    mock.handle = AsyncMock(
        return_value={
            "message": "The event date has not been announced yet.",
            "intent": "EVENT_CONTEXT",
            "tool": "get_event_context",
        }
    )
    return mock


@pytest.mark.asyncio
async def test_internal_chat_requires_token(agent):
    app = create_simulator_app(
        agent_factory=lambda: agent,
        internal_api_token="test-secret",
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        missing = await client.post(
            "/simulator/api/internal/chat",
            json={"message": "When is the event?"},
        )
        invalid = await client.post(
            "/simulator/api/internal/chat",
            headers={"Authorization": "Bearer wrong-secret"},
            json={"message": "When is the event?"},
        )

    assert missing.status_code == 401
    assert invalid.status_code == 401
    agent.handle.assert_not_awaited()


@pytest.mark.asyncio
async def test_internal_chat_accepts_valid_token(agent):
    app = create_simulator_app(
        agent_factory=lambda: agent,
        internal_api_token="test-secret",
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/simulator/api/internal/chat",
            headers={"Authorization": "Bearer test-secret"},
            json={"message": "When is the event?", "locale": "en"},
        )

    assert response.status_code == 200
    assert response.json()["trace"]["tool"] == "get_event_context"
    agent.handle.assert_awaited_once()


@pytest.mark.asyncio
async def test_internal_chat_disabled_without_token(agent):
    app = create_simulator_app(agent_factory=lambda: agent)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/simulator/api/internal/chat",
            json={"message": "Hello"},
        )

    assert response.status_code == 503
    agent.handle.assert_not_awaited()


@pytest.mark.asyncio
async def test_internal_rate_limit_does_not_block_public_simulator(agent):
    app = create_simulator_app(
        agent_factory=lambda: agent,
        internal_api_token="test-secret",
        internal_rate_limiter=ChatRateLimiter(max_requests=1),
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        first = await client.post(
            "/simulator/api/internal/chat",
            headers={"Authorization": "Bearer test-secret"},
            json={"message": "First"},
        )
        second = await client.post(
            "/simulator/api/internal/chat",
            headers={"Authorization": "Bearer test-secret"},
            json={"message": "Second"},
        )
        public = await client.post(
            "/simulator/api/chat",
            json={"message": "Public simulator question"},
        )

    assert first.status_code == 200
    assert second.status_code == 429
    assert public.status_code == 200
    assert agent.handle.await_count == 2
