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
    assert (
        "The centenary celebration date has not yet been"
        in response["message"]
    )

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

    assert "শতবর্ষ উদ্‌যাপনের মূল অনুষ্ঠানের তারিখ এখনো আনুষ্ঠানিকভাবে" in response["message"]


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


@pytest.mark.asyncio
async def test_assistance_requires_public_reference() -> None:
    reasoner = MagicMock()
    reasoner.reason = AsyncMock(
        return_value=AgentDecision(
            intent=AgentIntent.ASSISTANCE_CONTEXT,
            locale=SupportedLocale.BN,
        )
    )

    mcp_client = MagicMock()
    mcp_client.call_tool = AsyncMock()

    agent = SimulatorAgent(mcp_client=mcp_client, reasoner=reasoner)

    response = await agent.handle(
        message="কারও রক্তের প্রয়োজন আছে?",
        locale=SupportedLocale.BN,
    )

    assert "রেফারেন্স" in response["message"]
    assert response["tool"] is None
    mcp_client.call_tool.assert_not_awaited()


@pytest.mark.asyncio
async def test_assistance_lookup_and_followup() -> None:
    reasoner = MagicMock()
    reasoner.reason = AsyncMock(
        side_effect=[
            AgentDecision(
                intent=AgentIntent.ASSISTANCE_CONTEXT,
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
            is_error=False,
            structured_content={
                "public_reference": "HELP-2026-001",
                "assistance_type": "BLOOD",
                "status": "ACTIVE",
                "urgency": "URGENT",
                "summary": "A verified community member needs blood support.",
                "verified": True,
                "approved": True,
                "phone_number": "PRIVATE-PHONE",
            },
        )
    )

    agent = SimulatorAgent(mcp_client=mcp_client, reasoner=reasoner)

    first = await agent.handle(
        message="Check HELP-2026-001",
        session_id="session-1",
    )

    second = await agent.handle(
        message="Is that request still active?",
        session_id="session-1",
    )

    assert first["tool"] == "get_assistance_context"
    assert second["tool"] == "get_assistance_context"
    assert "PRIVATE-PHONE" not in first["message"]
    assert mcp_client.call_tool.await_count == 2


@pytest.mark.asyncio
async def test_unapproved_assistance_is_not_rendered() -> None:
    reasoner = MagicMock()
    reasoner.reason = AsyncMock(
        return_value=AgentDecision(
            intent=AgentIntent.ASSISTANCE_CONTEXT,
            locale=SupportedLocale.EN,
        )
    )

    mcp_client = MagicMock()
    mcp_client.call_tool = AsyncMock(
        return_value=MagicMock(
            is_error=False,
            structured_content={
                "public_reference": "HELP-2026-001",
                "status": "ACTIVE",
                "verified": True,
                "approved": False,
                "summary": "PRIVATE-UNAPPROVED-DATA",
            },
        )
    )

    agent = SimulatorAgent(mcp_client=mcp_client, reasoner=reasoner)

    response = await agent.handle(message="Check HELP-2026-001")

    assert response["tool"] is None
    assert "PRIVATE-UNAPPROVED-DATA" not in response["message"]
