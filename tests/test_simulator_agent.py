from unittest.mock import AsyncMock, MagicMock

import pytest

from community_mcp.agent.reasoning import AgentDecision
from community_mcp.agent.schemas import AgentIntent, SupportedLocale
from community_mcp.simulator.agent import SimulatorAgent


@pytest.mark.asyncio
async def test_event_answer_uses_mcp_data() -> None:
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
                "starts_at": None,
                "registration_enabled": False,
            }
        )
    )

    agent = SimulatorAgent(
        mcp_client=mcp_client,
        reasoner=reasoner,
    )

    response = await agent.handle(
        message="When is our centenary celebration?",
        locale=SupportedLocale.EN,
    )

    assert response["tool"] == "get_event_context"
    assert "not been announced" in response["message"]
    assert "not currently enabled" in response["message"]

    mcp_client.call_tool.assert_awaited_once_with(
        "get_event_context",
        {"event_slug": "centenary-celebration"},
    )


@pytest.mark.asyncio
async def test_bangla_event_answer() -> None:
    reasoner = MagicMock()
    reasoner.reason = AsyncMock(
        return_value=AgentDecision(
            intent=AgentIntent.EVENT_CONTEXT,
            locale=SupportedLocale.BN,
        )
    )

    mcp_client = MagicMock()
    mcp_client.call_tool = AsyncMock(
        return_value=MagicMock(
            structured_content={
                "title": "শতবর্ষ উদ্‌যাপন",
                "starts_at": None,
                "registration_enabled": False,
            }
        )
    )

    agent = SimulatorAgent(
        mcp_client=mcp_client,
        reasoner=reasoner,
    )

    response = await agent.handle(
        message="শতবর্ষ অনুষ্ঠান কবে?",
        locale=SupportedLocale.BN,
    )

    assert "তারিখ এখনো প্রকাশ করা হয়নি" in response["message"]


@pytest.mark.asyncio
async def test_non_event_intent_does_not_call_mcp() -> None:
    reasoner = MagicMock()
    reasoner.reason = AsyncMock(
        return_value=AgentDecision(
            intent=AgentIntent.UNKNOWN,
            locale=SupportedLocale.EN,
        )
    )

    mcp_client = MagicMock()
    mcp_client.call_tool = AsyncMock()

    agent = SimulatorAgent(
        mcp_client=mcp_client,
        reasoner=reasoner,
    )

    response = await agent.handle(message="Hello")

    assert response["tool"] is None
    mcp_client.call_tool.assert_not_awaited()
