from abc import ABC, abstractmethod

from community_mcp.schemas.event import EventDetail, EventSummary


class EventNotFoundError(Exception):
    pass


class CommunityProviderError(Exception):
    pass


class CommunityDataProvider(ABC):
    @abstractmethod
    async def list_events(self) -> list[EventSummary]:
        """Return publicly discoverable community events."""

    @abstractmethod
    async def get_event_by_slug(self, slug: str) -> EventDetail:
        """Return public details for one event."""
