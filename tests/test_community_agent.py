import pytest

from community_mcp.agent.community import CommunityAgent
from community_mcp.agent.schemas import (
    AgentIntent,
    AgentRequest,
    SupportedLocale,
)
from community_mcp.providers.demo import DemoProvider


@pytest.mark.asyncio
async def test_english_event_then_bangla_assistance_journey() -> None:
    agent = CommunityAgent(DemoProvider())

    event = await agent.handle(
        AgentRequest(
            message="What is the centenary event schedule?",
            locale=SupportedLocale.EN,
            actor_id="demo-member-001",
            session_id="journey-001",
        )
    )

    assert event.intent == AgentIntent.EVENT_CONTEXT
    assert "Centenary Celebration" in event.message

    assistance = await agent.handle(
        AgentRequest(
            message="কোনো জরুরি রক্তের অনুরোধ আছে?",
            locale=SupportedLocale.BN,
            actor_id="demo-member-001",
            session_id="journey-001",
        )
    )

    assert (
        assistance.intent
        == AgentIntent.ASSISTANCE_CONTEXT
    )
    assert "B+" in assistance.message

    prepared = await agent.handle(
        AgentRequest(
            message="I can donate blood",
            locale=SupportedLocale.EN,
            actor_id="demo-member-001",
            session_id="journey-001",
        )
    )

    assert (
        prepared.intent
        == AgentIntent.ASSISTANCE_RESPONSE
    )
    assert prepared.requires_confirmation is True
    assert prepared.preparation_id is not None

    session = agent.sessions.get("journey-001")
    assert session.pending_preparation_id is not None

    confirmed = await agent.handle(
        AgentRequest(
            message="হ্যাঁ নিশ্চিত করুন",
            locale=SupportedLocale.BN,
            actor_id="demo-member-001",
            session_id="journey-001",
        )
    )

    assert (
        confirmed.intent
        == AgentIntent.CONFIRM_ACTION
    )
    assert confirmed.requires_confirmation is False
    assert "রেকর্ড" in confirmed.message

    session = agent.sessions.get("journey-001")
    assert session.pending_preparation_id is None


@pytest.mark.asyncio
async def test_confirmation_without_pending_action_is_safe() -> None:
    agent = CommunityAgent(DemoProvider())

    response = await agent.handle(
        AgentRequest(
            message="Yes confirm",
            locale=SupportedLocale.EN,
            actor_id="demo-member-001",
            session_id="journey-002",
        )
    )

    assert response.intent == AgentIntent.CONFIRM_ACTION
    assert response.requires_confirmation is False
    assert "couldn't understand" in response.message.lower()
