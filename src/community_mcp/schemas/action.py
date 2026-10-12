from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from community_mcp.schemas.assistance import AssistanceAction


class PolicyDecision(StrEnum):
    REQUIRES_CONFIRMATION = "REQUIRES_CONFIRMATION"
    DENIED = "DENIED"


class PreparedAssistanceResponse(BaseModel):
    preparation_id: UUID
    public_reference: str
    actor_id: str
    action: AssistanceAction
    decision: PolicyDecision
    confirmation_required: bool
    confirmation_message: str
    policy_reasons: list[str]


class AssistanceResponseRecord(BaseModel):
    response_id: UUID
    preparation_id: UUID
    public_reference: str
    actor_id: str
    action: AssistanceAction
    recorded_at: datetime


class AuditReceipt(BaseModel):
    audit_id: UUID
    event_type: str
    actor_id: str
    public_reference: str
    action: AssistanceAction
    occurred_at: datetime


class ConfirmedAssistanceResponse(BaseModel):
    response: AssistanceResponseRecord
    audit: AuditReceipt
