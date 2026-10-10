import httpx
import pytest

from community_mcp.providers.credentials import (
    AccessTokenProvider,
    AccessTokenUnavailableError,
)
from community_mcp.providers.gotihub_member_context import (
    GotiHubMemberContextProvider,
)
from community_mcp.providers.member_context import (
    MemberContextUnavailableError,
)


class StubAccessTokenProvider(AccessTokenProvider):
    def __init__(
        self,
        tokens: dict[str, str] | None = None,
    ) -> None:
        self._tokens = tokens or {}

    async def get_access_token(self, actor_id: str) -> str:
        try:
            return self._tokens[actor_id]
        except KeyError as exc:
            raise AccessTokenUnavailableError(actor_id) from exc


@pytest.mark.asyncio
async def test_get_my_batch_context_uses_actor_scoped_bearer_token() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/members/me/batch-context"
        assert request.headers["Authorization"] == "Bearer actor-token-001"

        return httpx.Response(
            200,
            json={
                "batch_year": 2007,
                "registered_alumni_count": 23,
            },
        )

    credentials = StubAccessTokenProvider({"member-001": "actor-token-001"})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://community.example.org",
    ) as client:
        provider = GotiHubMemberContextProvider(
            "https://community.example.org",
            credentials,
            client=client,
        )

        context = await provider.get_my_batch_context("member-001")

    assert context.batch_year == 2007
    assert context.registered_alumni_count == 23


@pytest.mark.asyncio
async def test_missing_actor_credential_fails_closed_without_http_call() -> None:
    called = False

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, json={})

    credentials = StubAccessTokenProvider()

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://community.example.org",
    ) as client:
        provider = GotiHubMemberContextProvider(
            "https://community.example.org",
            credentials,
            client=client,
        )

        with pytest.raises(MemberContextUnavailableError):
            await provider.get_my_batch_context("unknown-member")

    assert called is False


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [401, 403, 404, 409])
async def test_private_context_failure_does_not_expose_platform_detail(
    status_code: int,
) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code,
            json={"detail": "private platform detail"},
        )

    credentials = StubAccessTokenProvider({"member-001": "actor-token-001"})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://community.example.org",
    ) as client:
        provider = GotiHubMemberContextProvider(
            "https://community.example.org",
            credentials,
            client=client,
        )

        with pytest.raises(MemberContextUnavailableError) as exc_info:
            await provider.get_my_batch_context("member-001")

    assert "private platform detail" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_invalid_member_context_response_fails_closed() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "batch_year": 2007,
                "registered_alumni_count": -1,
            },
        )

    credentials = StubAccessTokenProvider({"member-001": "actor-token-001"})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://community.example.org",
    ) as client:
        provider = GotiHubMemberContextProvider(
            "https://community.example.org",
            credentials,
            client=client,
        )

        with pytest.raises(MemberContextUnavailableError):
            await provider.get_my_batch_context("member-001")
