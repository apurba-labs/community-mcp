from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class AssistanceType(StrEnum):
    BLOOD = "BLOOD"
    MEDICAL_SUPPORT = "MEDICAL_SUPPORT"


class AssistanceStatus(StrEnum):
    OPEN = "OPEN"
    ACTIVE = "ACTIVE"
    FULFILLED = "FULFILLED"
    CLOSED = "CLOSED"


class AssistanceUrgency(StrEnum):
    STANDARD = "STANDARD"
    URGENT = "URGENT"
    CRITICAL = "CRITICAL"


class AssistanceAction(StrEnum):
    DONATE_BLOOD = "DONATE_BLOOD"
    VOLUNTEER = "VOLUNTEER"
    SHARE = "SHARE"


class AssistanceRequest(BaseModel):
    id: UUID
    public_reference: str
    assistance_type: AssistanceType
    status: AssistanceStatus

    title: str
    summary: str

    urgency: AssistanceUrgency
    location_text: str
    needed_by: datetime | None = None

    blood_group: str | None = None
    units_needed: int | None = None

    verified: bool
    approved: bool

    allowed_actions: list[AssistanceAction]
