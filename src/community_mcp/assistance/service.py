from community_mcp.providers.assistance import (
    AssistanceContextNotFoundError,
    AssistanceContextProvider,
    AssistanceContextUnavailableError,
)
from community_mcp.providers.demo_assistance import DemoAssistanceProvider
from community_mcp.schemas.assistance import AssistanceRequest


class AssistanceNotFoundError(Exception):
    pass


class AssistanceUnavailableError(Exception):
    pass


class AssistanceService:
    def __init__(
        self,
        provider: AssistanceContextProvider | None = None,
    ) -> None:
        self.provider = provider or DemoAssistanceProvider()

    async def get_public_context(
        self,
        public_reference: str,
    ) -> AssistanceRequest:
        try:
            return await self.provider.get_public_context(public_reference)
        except AssistanceContextNotFoundError as exc:
            raise AssistanceNotFoundError(public_reference) from exc
        except AssistanceContextUnavailableError as exc:
            raise AssistanceUnavailableError(public_reference) from exc

    async def get_member_context(
        self,
        public_reference: str,
        *,
        actor_id: str,
    ) -> AssistanceRequest:
        try:
            return await self.provider.get_member_context(
                public_reference,
                actor_id=actor_id,
            )
        except AssistanceContextNotFoundError as exc:
            raise AssistanceNotFoundError(public_reference) from exc
        except AssistanceContextUnavailableError as exc:
            raise AssistanceUnavailableError(public_reference) from exc
