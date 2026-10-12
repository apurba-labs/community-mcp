import pytest

from community_mcp.providers.demo_member_context import (
    DemoMemberContextProvider,
)
from community_mcp.providers.member_context import (
    MemberContextUnavailableError,
)


@pytest.mark.asyncio
async def test_demo_member_context_returns_safe_batch_aggregate() -> None:
    provider = DemoMemberContextProvider()

    context = await provider.get_my_batch_context("demo-member-001")

    assert context.batch_year == 2007
    assert context.registered_alumni_count == 23


@pytest.mark.asyncio
async def test_demo_member_context_rejects_unknown_actor() -> None:
    provider = DemoMemberContextProvider()

    with pytest.raises(MemberContextUnavailableError):
        await provider.get_my_batch_context("unknown-member")
