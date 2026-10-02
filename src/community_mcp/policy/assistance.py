from uuid import uuid4

from community_mcp.schemas.action import (
    PolicyDecision,
    PreparedAssistanceResponse,
)
from community_mcp.schemas.assistance import (
    AssistanceAction,
    AssistanceRequest,
    AssistanceStatus,
)


class AssistancePolicy:
    def prepare_response(
        self,
        request: AssistanceRequest,
        *,
        actor_id: str,
        action: AssistanceAction,
    ) -> PreparedAssistanceResponse:
        reasons: list[str] = []

        if not actor_id.strip():
            reasons.append("Actor identity is required.")

        if not request.verified:
            reasons.append("Assistance request is not verified.")

        if not request.approved:
            reasons.append("Assistance request is not approved.")

        if request.status not in {
            AssistanceStatus.OPEN,
            AssistanceStatus.ACTIVE,
        }:
            reasons.append("Assistance request is not active.")

        if action not in request.allowed_actions:
            reasons.append(
                f"Action '{action.value}' is not allowed for this request."
            )

        if reasons:
            return PreparedAssistanceResponse(
                preparation_id=uuid4(),
                public_reference=request.public_reference,
                actor_id=actor_id,
                action=action,
                decision=PolicyDecision.DENIED,
                confirmation_required=False,
                confirmation_message="",
                policy_reasons=reasons,
            )

        return PreparedAssistanceResponse(
            preparation_id=uuid4(),
            public_reference=request.public_reference,
            actor_id=actor_id,
            action=action,
            decision=PolicyDecision.REQUIRES_CONFIRMATION,
            confirmation_required=True,
            confirmation_message=(
                f"Confirm that you want to respond to "
                f"{request.public_reference} with action "
                f"{action.value}."
            ),
            policy_reasons=[
                "Assistance request is verified.",
                "Assistance request is approved.",
                "Assistance request is active.",
                "Requested action is allowed.",
                "Explicit user confirmation is required before any action.",
            ],
        )
