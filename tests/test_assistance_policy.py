import pytest

from community_mcp.assistance.service import AssistanceService
from community_mcp.policy.assistance import AssistancePolicy
from community_mcp.schemas.action import PolicyDecision
from community_mcp.schemas.assistance import AssistanceAction


@pytest.mark.asyncio
async def test_valid_response_requires_confirmation() -> None:
    request = await AssistanceService().get_public_context(
        "HELP-2026-001"
    )

    result = AssistancePolicy().prepare_response(
        request,
        actor_id="demo-member-001",
        action=AssistanceAction.DONATE_BLOOD,
    )

    assert result.decision == PolicyDecision.REQUIRES_CONFIRMATION
    assert result.confirmation_required is True
    assert result.action == AssistanceAction.DONATE_BLOOD
    assert result.public_reference == "HELP-2026-001"


@pytest.mark.asyncio
async def test_missing_actor_is_denied() -> None:
    request = await AssistanceService().get_public_context(
        "HELP-2026-001"
    )

    result = AssistancePolicy().prepare_response(
        request,
        actor_id="",
        action=AssistanceAction.DONATE_BLOOD,
    )

    assert result.decision == PolicyDecision.DENIED
    assert result.confirmation_required is False
    assert "Actor identity is required." in result.policy_reasons


@pytest.mark.asyncio
async def test_disallowed_action_is_denied() -> None:
    request = await AssistanceService().get_public_context(
        "HELP-2026-001"
    )

    request.allowed_actions = [AssistanceAction.SHARE]

    result = AssistancePolicy().prepare_response(
        request,
        actor_id="demo-member-001",
        action=AssistanceAction.DONATE_BLOOD,
    )

    assert result.decision == PolicyDecision.DENIED
    assert result.confirmation_required is False
