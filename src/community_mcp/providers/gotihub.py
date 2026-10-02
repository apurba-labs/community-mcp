import httpx
from pydantic import TypeAdapter, ValidationError

from community_mcp.providers.base import (
    CommunityDataProvider,
    CommunityProviderError,
    EventNotFoundError,
)
from community_mcp.schemas.event import EventDetail, EventSummary

_event_list_adapter = TypeAdapter(list[EventSummary])


class GotiHubProvider(CommunityDataProvider):
    def __init__(
        self,
        base_url: str,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client

    async def _get(self, path: str) -> httpx.Response:
        try:
            if self._client is not None:
                return await self._client.get(path)

            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=10.0,
            ) as client:
                return await client.get(path)
        except httpx.HTTPError as exc:
            raise CommunityProviderError("Unable to reach community platform") from exc

    async def list_events(self) -> list[EventSummary]:
        response = await self._get("/api/v1/events")

        if response.is_error:
            raise CommunityProviderError(
                f"Community platform returned HTTP {response.status_code}"
            )

        try:
            return _event_list_adapter.validate_python(response.json())
        except (ValueError, ValidationError) as exc:
            raise CommunityProviderError(
                "Community platform returned an invalid event response"
            ) from exc

    async def get_event_by_slug(self, slug: str) -> EventDetail:
        response = await self._get(f"/api/v1/events/slug/{slug}")

        if response.status_code == 404:
            raise EventNotFoundError(slug)

        if response.is_error:
            raise CommunityProviderError(
                f"Community platform returned HTTP {response.status_code}"
            )

        try:
            return EventDetail.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise CommunityProviderError(
                "Community platform returned an invalid event response"
            ) from exc
