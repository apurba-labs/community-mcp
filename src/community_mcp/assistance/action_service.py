from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from community_mcp.assistance.preparation_store import (
    AssistancePreparationStore,
)
from community_mcp.schemas.action import (
    AssistanceResponseRecord,
    AuditReceipt,
    ConfirmedAssistanceResponse,
    PolicyDecision,
    PreparedAssistanceResponse,
)


class ConfirmationRequiredError(Exception):
    pass


class ActorMismatchError(Exception):
    pass

class AssistanceActionStore(Protocol):
    def save(
        self,
        response: PreparedAssistanceResponse,
    ) -> PreparedAssistanceResponse: ...

    def confirm_response(
        self,
        preparation_id: UUID,
        *,
        actor_id: str,
        confirmed: bool,
    ) -> ConfirmedAssistanceResponse: ...

class AssistanceActionService:
    def __init__(
        self,
        preparation_store: AssistancePreparationStore,
        *,
        durable_store: AssistanceActionStore | None = None,
    ) -> None:
        self.preparation_store = preparation_store
        self.durable_store = durable_store

    def confirm_response(
        self,
        preparation_id: UUID,
        *,
        actor_id: str,
        confirmed: bool,
    ) -> ConfirmedAssistanceResponse:

        if self.durable_store is not None:
            return self.durable_store.confirm_response(
                preparation_id,
                actor_id=actor_id,
                confirmed=confirmed,
            )
        prepared = self.preparation_store.get(preparation_id)

        if prepared.decision != PolicyDecision.REQUIRES_CONFIRMATION:
            raise ConfirmationRequiredError(str(preparation_id))

        if not confirmed:
            raise ConfirmationRequiredError(str(preparation_id))

        if prepared.actor_id != actor_id:
            raise ActorMismatchError(actor_id)

        now = datetime.now(UTC)

        response = AssistanceResponseRecord(
            response_id=uuid4(),
            preparation_id=preparation_id,
            public_reference=prepared.public_reference,
            actor_id=actor_id,
            action=prepared.action,
            recorded_at=now,
        )

        audit = AuditReceipt(
            audit_id=uuid4(),
            event_type="ASSISTANCE_RESPONSE_RECORDED",
            actor_id=actor_id,
            public_reference=prepared.public_reference,
            action=prepared.action,
            occurred_at=now,
        )

        self.preparation_store.consume(preparation_id)

        return ConfirmedAssistanceResponse(
            response=response,
            audit=audit,
        )