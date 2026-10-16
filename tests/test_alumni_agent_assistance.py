from unittest.mock import AsyncMock

import pytest

from community_mcp.agent.schemas import AgentIntent, SupportedLocale
from community_mcp.providers.assistance import AssistanceContextNotFoundError
from community_mcp.schemas.assistance import (
    AssistanceAction,
    AssistanceRequest,
    AssistanceStatus,
    AssistanceType,
    AssistanceUrgency,
)
from community_mcp.simulator.alumni_agent import AlumniAgent


@pytest.fixture
def event_provider():
    provider = AsyncMock()
    provider.list_events.return_value = []
    return provider


@pytest.fixture
def assistance_provider():
    provider = AsyncMock()
    provider.get_public_context.return_value = AssistanceRequest(
        public_reference="HELP-2026-001",
        assistance_type=AssistanceType.BLOOD,
        status=AssistanceStatus.ACTIVE,
        summary="Urgent blood donation required.",
        urgency=AssistanceUrgency.URGENT,
        verified=True,
        approved=True,
        allowed_actions=[AssistanceAction.DONATE_BLOOD],
    )
    return provider


@pytest.mark.asyncio
async def test_public_assistance_reference(
    event_provider,
    assistance_provider,
):
    agent = AlumniAgent(
        provider=event_provider,
        assistance_provider=assistance_provider,
    )

    result = await agent.handle(
        message="HELP-2026-001 সম্পর্কে বলো",
        locale=SupportedLocale.BN,
    )

    assert result["intent"] == AgentIntent.ASSISTANCE_CONTEXT.value
    assert result["tool"] == "get_assistance_context"
    assert "HELP-2026-001" in result["message"]

    event_provider.list_events.assert_not_awaited()
    assistance_provider.get_public_context.assert_awaited_once_with("HELP-2026-001")


@pytest.mark.asyncio
async def test_assistance_question_requires_reference(
    event_provider,
    assistance_provider,
):
    agent = AlumniAgent(
        provider=event_provider,
        assistance_provider=assistance_provider,
    )

    result = await agent.handle(
        message="আমাদের কমিউনিটিতে কারও সাহায্যের প্রয়োজন আছে কি?",
        locale=SupportedLocale.BN,
    )

    assert result["intent"] == AgentIntent.ASSISTANCE_CONTEXT.value
    assert result["tool"] is None
    assert "HELP-2026-001" in result["message"]

    assistance_provider.get_public_context.assert_not_awaited()
    event_provider.list_events.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_assistance_reference_is_not_disclosed(
    event_provider,
    assistance_provider,
):
    assistance_provider.get_public_context.side_effect = AssistanceContextNotFoundError(
        "HELP-2026-999"
    )

    agent = AlumniAgent(
        provider=event_provider,
        assistance_provider=assistance_provider,
    )

    result = await agent.handle(
        message="HELP-2026-999",
        locale=SupportedLocale.EN,
    )

    assert result["intent"] == AgentIntent.ASSISTANCE_CONTEXT.value
    assert result["tool"] is None
    assert "unavailable" in result["message"].lower()

    event_provider.list_events.assert_not_awaited()


@pytest.mark.asyncio
async def test_unapproved_assistance_is_not_disclosed(
    event_provider,
    assistance_provider,
):
    assistance_provider.get_public_context.return_value = AssistanceRequest(
        public_reference="HELP-2026-001",
        assistance_type=AssistanceType.BLOOD,
        status=AssistanceStatus.ACTIVE,
        summary="Sensitive information",
        urgency=AssistanceUrgency.URGENT,
        verified=True,
        approved=False,
        allowed_actions=[],
    )

    agent = AlumniAgent(
        provider=event_provider,
        assistance_provider=assistance_provider,
    )

    result = await agent.handle(
        message="HELP-2026-001",
        locale=SupportedLocale.EN,
    )

    assert result["tool"] is None
    assert "Sensitive information" not in result["message"]

    event_provider.list_events.assert_not_awaited()
