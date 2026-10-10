from abc import ABC, abstractmethod

from pydantic import BaseModel

from community_mcp.agent.router import IntentRouter
from community_mcp.agent.schemas import (
    AgentIntent,
    SupportedLocale,
)
from community_mcp.schemas.assistance import AssistanceAction


class AgentDecision(BaseModel):
    intent: AgentIntent
    locale: SupportedLocale
    action: AssistanceAction | None = None


class ReasoningProvider(ABC):
    @abstractmethod
    async def reason(
        self,
        *,
        message: str,
        locale: SupportedLocale,
    ) -> AgentDecision:
        """Interpret user language into canonical agent intent."""


class DeterministicReasoner(ReasoningProvider):
    def __init__(
        self,
        router: IntentRouter | None = None,
    ) -> None:
        self.router = router or IntentRouter()

    async def reason(
        self,
        *,
        message: str,
        locale: SupportedLocale,
    ) -> AgentDecision:
        intent = self.router.classify(message)

        action = None
        if intent == AgentIntent.ASSISTANCE_RESPONSE:
            action = AssistanceAction.DONATE_BLOOD

        return AgentDecision(
            intent=intent,
            locale=locale,
            action=action,
        )
