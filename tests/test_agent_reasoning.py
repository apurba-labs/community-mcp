import pytest

from community_mcp.agent.reasoning import (
    AgentDecision,
    DeterministicReasoner,
)
from community_mcp.agent.schemas import (
    AgentIntent,
    SupportedLocale,
)
from community_mcp.schemas.assistance import AssistanceAction


@pytest.mark.asyncio
async def test_reasoner_returns_canonical_event_intent() -> None:
    decision = await DeterministicReasoner().reason(
        message="What is the centenary event schedule?",
        locale=SupportedLocale.EN,
    )

    assert decision.intent == AgentIntent.EVENT_CONTEXT
    assert decision.locale == SupportedLocale.EN
    assert decision.action is None


@pytest.mark.asyncio
async def test_reasoner_maps_bangla_donation_to_canonical_action() -> None:
    decision = await DeterministicReasoner().reason(
        message="আমি রক্ত দিতে পারি",
        locale=SupportedLocale.BN,
    )

    assert decision.intent == AgentIntent.ASSISTANCE_RESPONSE
    assert decision.action == AssistanceAction.DONATE_BLOOD


@pytest.mark.asyncio
async def test_unknown_reasoning_is_explicit() -> None:
    decision = await DeterministicReasoner().reason(
        message="Tell me something interesting",
        locale=SupportedLocale.EN,
    )

    assert decision.intent == AgentIntent.UNKNOWN
    assert decision.action is None


def test_reasoning_contract_has_no_authorization_field() -> None:
    fields = AgentDecision.model_fields

    assert "authorized" not in fields
    assert "approved" not in fields
    assert "confirmation_required" not in fields
