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
