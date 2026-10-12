from community_mcp.providers.member_context import (
    MemberContextProvider,
    MemberContextUnavailableError,
)
from community_mcp.schemas.community import MyBatchContext


class DemoMemberContextProvider(MemberContextProvider):
    """Synthetic member context for the public demo."""

    def __init__(self) -> None:
        self._contexts = {
            "demo-member-001": MyBatchContext(
                batch_year=2007,
                registered_alumni_count=23,
            )
        }

    async def get_my_batch_context(
        self,
        actor_id: str,
    ) -> MyBatchContext:
        context = self._contexts.get(actor_id)

        if context is None:
            raise MemberContextUnavailableError(actor_id)

        return context
