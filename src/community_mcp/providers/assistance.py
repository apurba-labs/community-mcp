from abc import ABC, abstractmethod

from community_mcp.schemas.assistance import AssistanceRequest


class AssistanceContextNotFoundError(Exception):
    pass


class AssistanceContextUnavailableError(Exception):
    pass


class AssistanceContextProvider(ABC):
    @abstractmethod
    async def get_public_context(
        self,
        public_reference: str,
    ) -> AssistanceRequest:
        """Return safe public context for a discoverable assistance request."""

    async def get_member_context(
        self,
        public_reference: str,
        *,
        actor_id: str,
    ) -> AssistanceRequest:
        return await self.get_public_context(public_reference)
