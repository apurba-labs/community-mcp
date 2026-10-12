from uuid import UUID

import httpx
import pytest

from community_mcp.providers.base import EventNotFoundError
from community_mcp.providers.gotihub import GotiHubProvider


@pytest.mark.asyncio
async def test_list_events_maps_public_response() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/events"

        return httpx.Response(
            200,
            json=[
                {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "title": "Centenary Celebration",
                    "slug": "centenary-celebration",
                    "short_description": "Celebrating 100 years.",
                    "event_type": "CENTENARY",
                    "starts_at": None,
                    "ends_at": None,
                    "timezone": "Asia/Dhaka",
                    "registration_enabled": True,
                    "capacity": None,
                    "cover": None,
                }
            ],
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://community.example.org",
    ) as client:
        provider = GotiHubProvider(
            "https://community.example.org",
            client=client,
        )

        events = await provider.list_events()

    assert len(events) == 1
    assert events[0].id == UUID("11111111-1111-1111-1111-111111111111")
    assert events[0].slug == "centenary-celebration"
    assert events[0].event_type == "CENTENARY"
    assert events[0].starts_at is None
    assert events[0].ends_at is None


@pytest.mark.asyncio
async def test_get_event_by_slug_maps_not_found() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/events/slug/missing-event"
        return httpx.Response(404, json={"detail": "Event not found"})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://community.example.org",
    ) as client:
        provider = GotiHubProvider(
            "https://community.example.org",
            client=client,
        )

        with pytest.raises(EventNotFoundError):
            await provider.get_event_by_slug("missing-event")


@pytest.mark.asyncio
async def test_service_token_only_sent_to_protected_event_endpoint() -> None:
    requests_seen = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests_seen.append(request)

        if request.url.path.endswith("/events"):
            return httpx.Response(200, json=[])

        return httpx.Response(404, json={"detail": "Not found"})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://community.example.org",
    ) as client:
        provider = GotiHubProvider(
            "https://community.example.org",
            organization_slug="test-school",
            service_token="synthetic-test-token",
            client=client,
        )

        await provider.list_events()

        with pytest.raises(EventNotFoundError):
            await provider.get_event_by_slug("missing-event")

    assert requests_seen[0].url.path == (
        "/api/v1/integrations/community/organizations/test-school/events"
    )
    assert requests_seen[0].headers["Authorization"] == ("Bearer synthetic-test-token")

    assert requests_seen[1].url.path == "/api/v1/events/slug/missing-event"
    assert "Authorization" not in requests_seen[1].headers
