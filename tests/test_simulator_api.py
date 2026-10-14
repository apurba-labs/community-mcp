from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from community_mcp.simulator.api import ChatRateLimiter, create_simulator_app
from community_mcp.usage.store import SQLiteUsageStore, UsageBudget


@pytest.fixture
def usage_controls(tmp_path):
    """Provide isolated persistent usage controls for each test."""
    store = SQLiteUsageStore(tmp_path / "usage.sqlite3")

    budget = UsageBudget(
        daily_requests=100,
        concurrent_requests=10,
        daily_tokens=100_000,
    )

    return {
        "usage_store": store,
        "public_budget": budget,
        "alumni_budget": budget,
    }


@pytest.mark.asyncio
async def test_chat_endpoint_returns_answer_and_trace(usage_controls):
    agent = MagicMock()
    agent.handle = AsyncMock(
        return_value={
            "message": "The event date has not been announced yet.",
            "intent": "EVENT_CONTEXT",
            "tool": "get_event_context",
        }
    )

    app = create_simulator_app(
        agent_factory=lambda: agent,
        **usage_controls,
    )

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

    summary = usage_controls["usage_store"].summary(channel="public")
    assert summary["total_requests"] == 1
    assert summary["reserved_requests"] == 0


@pytest.mark.asyncio
async def test_chat_rejects_empty_message(usage_controls):
    app = create_simulator_app(
        agent_factory=lambda: MagicMock(),
        **usage_controls,
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/simulator/api/chat",
            json={"message": ""},
        )

    assert response.status_code == 422

    summary = usage_controls["usage_store"].summary(channel="public")
    assert summary["total_requests"] == 0


@pytest.mark.asyncio
async def test_chat_rate_limit(usage_controls):
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
        **usage_controls,
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

    assert first.status_code == 200, first.json()
    assert second.status_code == 429
    assert agent.handle.await_count == 1

    summary = usage_controls["usage_store"].summary(channel="public")
    assert summary["total_requests"] == 1