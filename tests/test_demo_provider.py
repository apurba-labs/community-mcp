import pytest

from community_mcp.providers.base import EventNotFoundError
from community_mcp.providers.demo import DemoProvider


@pytest.mark.asyncio
async def test_demo_provider_lists_events() -> None:
    provider = DemoProvider()

    events = await provider.list_events()

    assert len(events) >= 1
    assert events[0].slug == "centenary-celebration"


@pytest.mark.asyncio
async def test_demo_provider_returns_event_detail() -> None:
    provider = DemoProvider()

    event = await provider.get_event_by_slug("centenary-celebration")

    assert event.event_type == "CENTENARY"
    assert len(event.program) == 3
    assert event.program[0].title == "Alumni Gathering"


@pytest.mark.asyncio
async def test_demo_provider_maps_not_found() -> None:
    provider = DemoProvider()

    with pytest.raises(EventNotFoundError):
        await provider.get_event_by_slug("does-not-exist")
