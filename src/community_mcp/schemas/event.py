from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

EventType = Literal[
    "ALUMNI_GATHERING",
    "CENTENARY",
    "REUNION",
    "CEREMONY",
    "MEETING",
    "CULTURAL",
    "OTHER",
]


class EventMedia(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    media_type: str
    url: str
    title: str | None
    alt_text: str | None
    sort_order: int
    is_featured: bool


class EventVenue(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    name: str
    address: str | None
    location_notes: str | None
    is_primary: bool


class EventSchedule(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    title: str
    description: str | None
    schedule_type: str
    starts_at: datetime | None
    starts_at: datetime | None
    venue_id: UUID | None
    location_text: str | None
    registration_required: bool
    capacity: int | None
    sort_order: int


class EventSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    title: str
    slug: str
    short_description: str | None
    event_type: EventType
    starts_at: datetime | None
    ends_at: datetime | None
    timezone: str
    registration_enabled: bool
    capacity: int | None
    cover: EventMedia | None = None


class EventPerson(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    display_name: str
    name_bn: str | None
    profile_image_url: str | None


class EventGuest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    person: EventPerson
    guest_title: str | None
    guest_title_bn: str | None
    designation: str | None
    designation_bn: str | None
    sort_order: int


class EventSponsor(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    name: str
    name_bn: str | None
    tier: str
    display_label: str | None
    logo_url: str | None
    website_url: str | None
    description: str | None
    sort_order: int


class EventTeamMember(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    person: EventPerson
    position_title: str
    position_title_bn: str | None
    sort_order: int


class EventDetail(EventSummary):
    description: str | None
    registration_starts_at: datetime | None
    registration_ends_at: datetime | None
    primary_venue: EventVenue | None = None
    media: list[EventMedia]
    program: list[EventSchedule]
    guests: list[EventGuest]
    sponsors: list[EventSponsor]
    event_team: list[EventTeamMember]
