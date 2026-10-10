import sqlite3
from uuid import UUID

import pytest

from community_mcp.agent.community import CommunityAgent
from community_mcp.agent.reasoning import (
    AgentDecision,
    ReasoningProvider,
)
from community_mcp.agent.schemas import (
    AgentIntent,
    AgentRequest,
    SupportedLocale,
)
from community_mcp.assistance.preparation_store import (
    PreparationAlreadyConsumedError,
)
from community_mcp.assistance.sqlite_store import SQLiteAssistanceStore
from community_mcp.providers.demo import DemoProvider
from community_mcp.schemas.assistance import AssistanceAction


@pytest.mark.asyncio
async def test_english_event_then_bangla_assistance_journey() -> None:
    agent = CommunityAgent(
        DemoProvider(),
        allow_demo_actions=True,
    )

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

    assert assistance.intent == AgentIntent.ASSISTANCE_CONTEXT
    assert "B+" in assistance.message

    prepared = await agent.handle(
        AgentRequest(
            message="I can donate blood",
            locale=SupportedLocale.EN,
            actor_id="demo-member-001",
            session_id="journey-001",
        )
    )

    assert prepared.intent == AgentIntent.ASSISTANCE_RESPONSE
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

    assert confirmed.intent == AgentIntent.CONFIRM_ACTION
    assert confirmed.requires_confirmation is False
    assert "রেকর্ড" in confirmed.message

    session = agent.sessions.get("journey-001")
    assert session.pending_preparation_id is None


@pytest.mark.asyncio
async def test_confirmation_without_pending_action_is_safe() -> None:
    agent = CommunityAgent(
        DemoProvider(),
        allow_demo_actions=True,
    )

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
    assert "no pending action" in response.message.lower()


@pytest.mark.asyncio
async def test_bangla_confirmation_without_pending_action_is_safe() -> None:
    agent = CommunityAgent(
        DemoProvider(),
        allow_demo_actions=True,
    )

    response = await agent.handle(
        AgentRequest(
            message="হ্যাঁ নিশ্চিত করুন",
            locale=SupportedLocale.BN,
            actor_id="demo-member-001",
            session_id="journey-003",
        )
    )

    assert response.intent == AgentIntent.CONFIRM_ACTION
    assert response.requires_confirmation is False
    assert "প্রস্তুত কার্যক্রম নেই" in response.message


class NaturalLanguageTestReasoner(ReasoningProvider):
    async def reason(
        self,
        *,
        message: str,
        locale: SupportedLocale,
    ) -> AgentDecision:
        return AgentDecision(
            intent=AgentIntent.ASSISTANCE_RESPONSE,
            locale=locale,
            action=AssistanceAction.DONATE_BLOOD,
        )


@pytest.mark.asyncio
async def test_agent_uses_injected_reasoner_for_natural_language() -> None:
    agent = CommunityAgent(
        DemoProvider(),
        reasoner=NaturalLanguageTestReasoner(),
        allow_demo_actions=True,
    )

    response = await agent.handle(
        AgentRequest(
            message="I'm B positive and would be happy to help them.",
            locale=SupportedLocale.EN,
            actor_id="demo-member-001",
            session_id="reasoning-001",
        )
    )

    assert response.intent == AgentIntent.ASSISTANCE_RESPONSE
    assert response.requires_confirmation is True
    assert response.preparation_id is not None


@pytest.mark.asyncio
async def test_bangla_community_context_uses_member_aggregate() -> None:
    from community_mcp.providers.demo_member_context import (
        DemoMemberContextProvider,
    )

    agent = CommunityAgent(
        DemoProvider(),
        member_context_provider=DemoMemberContextProvider(),
    )

    response = await agent.handle(
        AgentRequest(
            message="আমার ব্যাচের কতজন অ্যালামনাই রেজিস্ট্রেশন করেছে?",
            locale=SupportedLocale.BN,
            actor_id="demo-member-001",
            session_id="community-001",
        )
    )

    assert response.intent == AgentIntent.COMMUNITY_CONTEXT
    assert "2007" in response.message
    assert "23" in response.message


@pytest.mark.asyncio
async def test_community_context_without_actor_fails_closed() -> None:
    from community_mcp.providers.demo_member_context import (
        DemoMemberContextProvider,
    )

    agent = CommunityAgent(
        DemoProvider(),
        member_context_provider=DemoMemberContextProvider(),
    )

    response = await agent.handle(
        AgentRequest(
            message="How many alumni from my batch are registered?",
            locale=SupportedLocale.EN,
            actor_id=None,
            session_id="community-002",
        )
    )

    assert response.intent == AgentIntent.COMMUNITY_CONTEXT
    assert "cannot be securely resolved" in response.message


@pytest.mark.asyncio
async def test_agent_durable_confirmation_survives_restart(tmp_path) -> None:
    database = tmp_path / "agent-assistance.sqlite3"

    agent = CommunityAgent(
        DemoProvider(),
        durable_store=SQLiteAssistanceStore(database),
        allow_demo_actions=True,
    )

    prepared = await agent.handle(
        AgentRequest(
            message="I can donate blood",
            locale=SupportedLocale.EN,
            actor_id="demo-member-001",
            session_id="durable-001",
        )
    )

    assert prepared.requires_confirmation is True
    assert prepared.preparation_id is not None

    preparation_id = UUID(prepared.preparation_id)

    confirmed = await agent.handle(
        AgentRequest(
            message="Yes confirm",
            locale=SupportedLocale.EN,
            actor_id="demo-member-001",
            session_id="durable-001",
        )
    )

    assert confirmed.intent == AgentIntent.CONFIRM_ACTION
    assert confirmed.requires_confirmation is False

    restarted_store = SQLiteAssistanceStore(database)

    with sqlite3.connect(database) as connection:
        response_count = connection.execute("SELECT COUNT(*) FROM responses").fetchone()[0]

        audit_count = connection.execute("SELECT COUNT(*) FROM audit_receipts").fetchone()[0]

    assert response_count == 1
    assert audit_count == 1

    with pytest.raises(PreparationAlreadyConsumedError):
        restarted_store.confirm_response(
            preparation_id,
            actor_id="demo-member-001",
            confirmed=True,
        )
