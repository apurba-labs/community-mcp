from community_mcp.agent.reasoning import (
    AgentDecision,
    ReasoningProvider,
)
from community_mcp.agent.schemas import (
    AgentIntent,
    SupportedLocale,
)


class ConfirmationGate:
    """Deterministic boundary for consequential confirmation intent."""

    _EXPLICIT_CONFIRMATIONS = {
        "yes confirm",
        "yes, confirm it",
        "confirm",
        "confirm it",
        "i confirm",
        "হ্যাঁ নিশ্চিত করুন",
        "হ্যাঁ, নিশ্চিত করুন",
        "হ্যাঁ, আমি নিশ্চিত করছি",
        "নিশ্চিত করুন",
    }

    def is_explicit_confirmation(self, message: str) -> bool:
        return message.casefold().strip() in self._EXPLICIT_CONFIRMATIONS


class SafeReasoner(ReasoningProvider):
    """Guards consequential intents around a delegated reasoner."""

    def __init__(
        self,
        delegate: ReasoningProvider,
        *,
        confirmation_gate: ConfirmationGate | None = None,
    ) -> None:
        self.delegate = delegate
        self.confirmation_gate = (
            confirmation_gate or ConfirmationGate()
        )

    async def reason(
        self,
        *,
        message: str,
        locale: SupportedLocale,
    ) -> AgentDecision:
        if self.confirmation_gate.is_explicit_confirmation(message):
            return AgentDecision(
                intent=AgentIntent.CONFIRM_ACTION,
                locale=locale,
                action=None,
            )

        decision = await self.delegate.reason(
            message=message,
            locale=locale,
        )

        # The delegated model may interpret language, but it cannot
        # elevate a non-explicit message into confirmation.
        if decision.intent == AgentIntent.CONFIRM_ACTION:
            return AgentDecision(
                intent=AgentIntent.UNKNOWN,
                locale=locale,
                action=None,
            )

        return decision