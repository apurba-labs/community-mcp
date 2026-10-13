from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from community_mcp.simulator.api import ChatRateLimiter, create_simulator_app


@pytest.mark.asyncio
async def test_chat_endpoint_returns_answer_and_trace():
    agent = MagicMock()
    agent.handle = AsyncMock(
        return_value={
            "message": "The event date has not been announced yet.",
            "intent": "EVENT_CONTEXT",
            "tool": "get_event_context",
        }
    )

    app = create_simulator_app(agent_factory=lambda: agent)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/simulator/api/chat",
            json={
                "message": "When is the centenary celebration?",
                "locale": "en",
            },
        )

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["trace"]["tool"] == "get_event_context"
    assert body["trace"]["authenticated"] is True
    assert body["message"] == "The event date has not been announced yet."
    assert body["session_id"]


@pytest.mark.asyncio
async def test_chat_rejects_empty_message():
    app = create_simulator_app(agent_factory=lambda: MagicMock())

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/simulator/api/chat",
            json={"message": ""},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_rate_limit():
    agent = MagicMock()
    agent.handle = AsyncMock(
        return_value={
            "message": "OK",
            "intent": "EVENT_CONTEXT",
            "tool": "get_event_context",
        }
    )

    app = create_simulator_app(
        agent_factory=lambda: agent,
        rate_limiter=ChatRateLimiter(max_requests=1),
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        first = await client.post(
            "/simulator/api/chat",
            json={"message": "Hello"},
        )
        second = await client.post(
            "/simulator/api/chat",
            json={"message": "Hello again"},
        )

    assert first.status_code == 200
    assert second.status_code == 429
    assert agent.handle.await_count == 1
