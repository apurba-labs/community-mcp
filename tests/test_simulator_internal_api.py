from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from community_mcp.simulator.api import ChatRateLimiter, create_simulator_app
from community_mcp.usage.store import SQLiteUsageStore, UsageBudget

ORGANIZATION_ID = "11111111-1111-4111-8111-111111111111"


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


@pytest.fixture
def usage_controls(tmp_path):
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
async def test_internal_chat_requires_token(agent, usage_controls):
    app = create_simulator_app(
        agent_factory=lambda: agent, internal_api_token="test-secret", **usage_controls
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        missing = await client.post(
            "/simulator/api/internal/chat",
            json={
                "message": "When is the event?",
                "organization_id": ORGANIZATION_ID,
            },
        )
        invalid = await client.post(
            "/simulator/api/internal/chat",
            headers={"Authorization": "Bearer wrong-secret"},
            json={
                "message": "When is the event?",
                "organization_id": ORGANIZATION_ID,
            },
        )

    assert missing.status_code == 401
    assert invalid.status_code == 401
    agent.handle.assert_not_awaited()


@pytest.mark.asyncio
async def test_internal_chat_accepts_valid_token(agent, usage_controls):
    app = create_simulator_app(
        agent_factory=lambda: agent, internal_api_token="test-secret", **usage_controls
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/simulator/api/internal/chat",
            headers={"Authorization": "Bearer test-secret"},
            json={
                "message": "When is the event?",
                "locale": "en",
                "organization_id": ORGANIZATION_ID,
            },
        )

    assert response.status_code == 200
    assert response.json()["trace"]["tool"] == "get_event_context"
    agent.handle.assert_awaited_once()


@pytest.mark.asyncio
async def test_internal_chat_disabled_without_token(agent, usage_controls):
    app = create_simulator_app(agent_factory=lambda: agent, **usage_controls)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/simulator/api/internal/chat",
            json={
                "message": "Hello",
                "organization_id": ORGANIZATION_ID,
            },
        )

    assert response.status_code == 503
    agent.handle.assert_not_awaited()


@pytest.mark.asyncio
async def test_internal_rate_limit_does_not_block_public_simulator(agent, usage_controls):
    app = create_simulator_app(
        agent_factory=lambda: agent,
        internal_api_token="test-secret",
        internal_rate_limiter=ChatRateLimiter(max_requests=1),
        **usage_controls,
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        first = await client.post(
            "/simulator/api/internal/chat",
            headers={"Authorization": "Bearer test-secret"},
            json={
                "message": "First",
                "organization_id": ORGANIZATION_ID,
            },
        )

        second = await client.post(
            "/simulator/api/internal/chat",
            headers={"Authorization": "Bearer test-secret"},
            json={
                "message": "Second",
                "organization_id": ORGANIZATION_ID,
            },
        )
        public = await client.post(
            "/simulator/api/chat",
            json={"message": "Public simulator question"},
        )

    assert first.status_code == 200
    assert second.status_code == 429
    assert public.status_code == 200
    assert agent.handle.await_count == 2


@pytest.mark.asyncio
async def test_internal_chat_rejects_other_organization(agent, usage_controls):
    app = create_simulator_app(
        agent_factory=lambda: agent,
        internal_api_token="test-secret",
        internal_organization_id=ORGANIZATION_ID,
        **usage_controls,
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/simulator/api/internal/chat",
            headers={"Authorization": "Bearer test-secret"},
            json={
                "message": "When is the event?",
                "organization_id": "22222222-2222-4222-8222-222222222222",
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"] == ("Organization is not authorized for this assistant.")
    agent.handle.assert_not_awaited()


@pytest.mark.asyncio
async def test_internal_chat_accepts_matching_organization(agent, usage_controls):
    app = create_simulator_app(
        agent_factory=lambda: agent,
        internal_api_token="test-secret",
        internal_organization_id=ORGANIZATION_ID,
        **usage_controls,
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/simulator/api/internal/chat",
            headers={"Authorization": "Bearer test-secret"},
            json={
                "message": "When is the event?",
                "organization_id": ORGANIZATION_ID,
            },
        )

    assert response.status_code == 200
    agent.handle.assert_awaited_once()


@pytest.mark.asyncio
async def test_internal_chat_uses_alumni_agent(agent, usage_controls):
    public_agent = MagicMock()
    public_agent.handle = AsyncMock()

    app = create_simulator_app(
        agent_factory=lambda: public_agent,
        internal_agent_factory=lambda: agent,
        internal_api_token="test-secret",
        internal_organization_id=ORGANIZATION_ID,
        **usage_controls,
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/simulator/api/internal/chat",
            headers={"Authorization": "Bearer test-secret"},
            json={
                "message": "When is the event?",
                "organization_id": ORGANIZATION_ID,
            },
        )

    assert response.status_code == 200
    agent.handle.assert_awaited_once()
    public_agent.handle.assert_not_awaited()
