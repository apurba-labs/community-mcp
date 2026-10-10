import pytest

from community_mcp.agent.reasoning import (
    AgentDecision,
    ReasoningProvider,
)
from community_mcp.agent.safe_reasoning import (
    ConfirmationGate,
    SafeReasoner,
)
from community_mcp.agent.schemas import (
    AgentIntent,
    SupportedLocale,
)


class FalseConfirmationReasoner(ReasoningProvider):
    async def reason(
        self,
        *,
        message: str,
        locale: SupportedLocale,
    ) -> AgentDecision:
        return AgentDecision(
            intent=AgentIntent.CONFIRM_ACTION,
            locale=locale,
            action=None,
        )


class EventReasoner(ReasoningProvider):
    async def reason(
        self,
        *,
        message: str,
        locale: SupportedLocale,
    ) -> AgentDecision:
        return AgentDecision(
            intent=AgentIntent.EVENT_CONTEXT,
            locale=locale,
            action=None,
        )


@pytest.mark.parametrize(
    "message",
    [
        "Yes confirm",
        "Yes, confirm it",
        "I confirm",
        "হ্যাঁ নিশ্চিত করুন",
        "হ্যাঁ, নিশ্চিত করুন",
        "হ্যাঁ, আমি নিশ্চিত করছি",
        "নিশ্চিত করুন",
    ],
)
def test_confirmation_gate_accepts_explicit_confirmation(
    message: str,
) -> None:
    assert ConfirmationGate().is_explicit_confirmation(message)


@pytest.mark.parametrize(
    "message",
    [
        "yes",
        "okay",
        "হ্যাঁ",
        "ঠিক আছে",
    ],
)
def test_confirmation_gate_rejects_generic_affirmative(
    message: str,
) -> None:
    assert not ConfirmationGate().is_explicit_confirmation(message)


@pytest.mark.asyncio
async def test_safe_reasoner_blocks_model_false_confirmation() -> None:
    reasoner = SafeReasoner(FalseConfirmationReasoner())

    decision = await reasoner.reason(
        message="হ্যাঁ",
        locale=SupportedLocale.BN,
    )

    assert decision.intent == AgentIntent.UNKNOWN
    assert decision.action is None


@pytest.mark.asyncio
async def test_safe_reasoner_accepts_explicit_confirmation() -> None:
    reasoner = SafeReasoner(EventReasoner())

    decision = await reasoner.reason(
        message="হ্যাঁ নিশ্চিত করুন",
        locale=SupportedLocale.BN,
    )

    assert decision.intent == AgentIntent.CONFIRM_ACTION
    assert decision.action is None


@pytest.mark.asyncio
async def test_safe_reasoner_preserves_non_confirmation_decision() -> None:
    reasoner = SafeReasoner(EventReasoner())

    decision = await reasoner.reason(
        message="What is the event schedule?",
        locale=SupportedLocale.EN,
    )

    assert decision.intent == AgentIntent.EVENT_CONTEXT
