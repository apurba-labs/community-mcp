import httpx
from pydantic import ValidationError

from community_mcp.providers.credentials import (
    AccessTokenProvider,
    AccessTokenUnavailableError,
)
from community_mcp.providers.member_context import (
    MemberContextProvider,
    MemberContextUnavailableError,
)
from community_mcp.schemas.community import MyBatchContext


class GotiHubMemberContextProvider(MemberContextProvider):
    def __init__(
        self,
        base_url: str,
        credential_provider: AccessTokenProvider,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._credential_provider = credential_provider
        self._client = client

    async def _get(
        self,
        path: str,
        *,
        access_token: str,
    ) -> httpx.Response:
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            if self._client is not None:
                return await self._client.get(path, headers=headers)

            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=10.0,
            ) as client:
                return await client.get(path, headers=headers)
        except httpx.HTTPError as exc:
            raise MemberContextUnavailableError(
                "Unable to reach community platform"
            ) from exc

    async def get_my_batch_context(
        self,
        actor_id: str,
    ) -> MyBatchContext:
        try:
            access_token = await self._credential_provider.get_access_token(
                actor_id
            )
        except AccessTokenUnavailableError as exc:
            raise MemberContextUnavailableError(actor_id) from exc

        if not access_token.strip():
            raise MemberContextUnavailableError(actor_id)

        response = await self._get(
            "/api/v1/members/me/batch-context",
            access_token=access_token,
        )

        if response.status_code in {401, 403, 404, 409}:
            raise MemberContextUnavailableError(actor_id)

        if response.is_error:
            raise MemberContextUnavailableError(
                f"Community platform returned HTTP {response.status_code}"
            )

        try:
            return MyBatchContext.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise MemberContextUnavailableError(
                "Community platform returned invalid member context"
            ) from exc
