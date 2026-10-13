from unittest.mock import AsyncMock, MagicMock

import pytest

from community_mcp.agent.reasoning import AgentDecision
from community_mcp.agent.schemas import AgentIntent, SupportedLocale
from community_mcp.simulator.agent import SimulatorAgent


@pytest.mark.asyncio
async def test_followup_uses_event_context_and_fresh_mcp_data():
    reasoner = MagicMock()
    reasoner.reason = AsyncMock(
        side_effect=[
            AgentDecision(
                intent=AgentIntent.EVENT_CONTEXT,
                locale=SupportedLocale.EN,
            ),
            AgentDecision(
                intent=AgentIntent.UNKNOWN,
                locale=SupportedLocale.EN,
            ),
        ]
    )

    mcp_client = MagicMock()
    mcp_client.call_tool = AsyncMock(
        return_value=MagicMock(
            structured_content={
                "title": "Centenary Celebration",
                "starts_at": None,
                "registration_enabled": False,
            }
        )
    )

    agent = SimulatorAgent(mcp_client=mcp_client, reasoner=reasoner)

    first = await agent.handle(
        message="When is the centenary celebration?",
        session_id="test-session",
    )

    second = await agent.handle(
        message="What about registration?",
        session_id="test-session",
    )

    assert "not been announced" in first["message"]
    assert "not currently enabled" in second["message"]
    assert mcp_client.call_tool.await_count == 2


@pytest.mark.asyncio
async def test_followup_without_context_is_not_assumed_to_be_event():
    reasoner = MagicMock()
    reasoner.reason = AsyncMock(
        return_value=AgentDecision(
            intent=AgentIntent.UNKNOWN,
            locale=SupportedLocale.EN,
        )
    )

    mcp_client = MagicMock()
    mcp_client.call_tool = AsyncMock()

    agent = SimulatorAgent(mcp_client=mcp_client, reasoner=reasoner)

    result = await agent.handle(
        message="What about registration?",
        session_id="new-session",
    )

    assert result["tool"] is None
    mcp_client.call_tool.assert_not_awaited()


@pytest.mark.asyncio
async def test_venue_answer_uses_authoritative_mcp_field():
    reasoner = MagicMock()
    reasoner.reason = AsyncMock(
        return_value=AgentDecision(
            intent=AgentIntent.EVENT_CONTEXT,
            locale=SupportedLocale.EN,
        )
    )

    mcp_client = MagicMock()
    mcp_client.call_tool = AsyncMock(
        return_value=MagicMock(
            structured_content={
                "title": "Centenary Celebration",
                "primary_venue": {
                    "name": "School Campus (proposed)",
                },
            }
        )
    )

    agent = SimulatorAgent(mcp_client=mcp_client, reasoner=reasoner)

    result = await agent.handle(
        message="Where is the centenary celebration?",
        session_id="venue-session",
    )

    assert "School Campus (proposed)" in result["message"]
