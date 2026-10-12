from abc import ABC, abstractmethod


class AccessTokenUnavailableError(Exception):
    """Raised when no authenticated credential is available for an actor."""


class AccessTokenProvider(ABC):
    @abstractmethod
    async def get_access_token(self, actor_id: str) -> str:
        """Return an actor-scoped access token supplied by the runtime boundary."""
