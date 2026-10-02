import json
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from community_mcp.providers.base import (
    CommunityDataProvider,
    CommunityProviderError,
    EventNotFoundError,
)
from community_mcp.schemas.event import EventDetail, EventSummary

_event_detail_list_adapter = TypeAdapter(list[EventDetail])


class DemoProvider(CommunityDataProvider):
    def __init__(self, fixture_path: Path | None = None) -> None:
        self._fixture_path = fixture_path or (
            Path(__file__).resolve().parents[3] / "demo" / "fixtures" / "events.json"
        )

    def _load_events(self) -> list[EventDetail]:
        try:
            payload = json.loads(self._fixture_path.read_text(encoding="utf-8"))
            return _event_detail_list_adapter.validate_python(payload)
        except (OSError, ValueError, ValidationError) as exc:
            raise CommunityProviderError("Unable to load demo event data") from exc

    async def list_events(self) -> list[EventSummary]:
        return [
            EventSummary.model_validate(event.model_dump())
            for event in self._load_events()
        ]

    async def get_event_by_slug(self, slug: str) -> EventDetail:
        for event in self._load_events():
            if event.slug == slug:
                return event

        raise EventNotFoundError(slug)
