from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class AssistanceType(StrEnum):
    BLOOD = "BLOOD"
    FINANCIAL_SUPPORT = "FINANCIAL_SUPPORT"
    MEDICAL_SUPPORT = "MEDICAL_SUPPORT"
    FAMILY_SUPPORT = "FAMILY_SUPPORT"
    EMERGENCY = "EMERGENCY"
    OTHER = "OTHER"


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
    CONTRIBUTE = "CONTRIBUTE"
    VOLUNTEER = "VOLUNTEER"
    SHARE = "SHARE"


class AssistanceRequest(BaseModel):
    public_reference: str
    assistance_type: AssistanceType
    status: AssistanceStatus = AssistanceStatus.ACTIVE

    title: str | None = None
    summary: str | None = None

    urgency: AssistanceUrgency
    location_text: str | None = None
    needed_by: datetime | None = None

    blood_group: str | None = None
    units_needed: int | None = None

    verified: bool = True
    approved: bool = True

    allowed_actions: list[AssistanceAction]
