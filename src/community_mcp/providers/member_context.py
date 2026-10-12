from abc import ABC, abstractmethod

from community_mcp.schemas.community import MyBatchContext


class MemberContextUnavailableError(Exception):
    """Raised when authenticated member context cannot be resolved."""


class MemberContextProvider(ABC):
    @abstractmethod
    async def get_my_batch_context(
        self,
        actor_id: str,
    ) -> MyBatchContext:
        """Return safe aggregate context for the authenticated member."""
