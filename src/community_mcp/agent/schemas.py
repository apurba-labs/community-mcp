from enum import StrEnum

from pydantic import BaseModel


class SupportedLocale(StrEnum):
    EN = "en"
    BN = "bn"


class AgentIntent(StrEnum):
    EVENT_CONTEXT = "EVENT_CONTEXT"
    ASSISTANCE_CONTEXT = "ASSISTANCE_CONTEXT"
    ASSISTANCE_RESPONSE = "ASSISTANCE_RESPONSE"
    CONFIRM_ACTION = "CONFIRM_ACTION"
    UNKNOWN = "UNKNOWN"


class AgentRequest(BaseModel):
    message: str
    locale: SupportedLocale
    actor_id: str | None = None
    session_id: str


class AgentResponse(BaseModel):
    locale: SupportedLocale
    intent: AgentIntent
    message: str
    requires_confirmation: bool = False
    preparation_id: str | None = None
