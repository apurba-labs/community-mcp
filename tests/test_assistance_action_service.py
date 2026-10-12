import pytest

from community_mcp.assistance.action_service import (
    ActorMismatchError,
    AssistanceActionService,
    ConfirmationRequiredError,
)
from community_mcp.assistance.preparation_store import (
    AssistancePreparationStore,
    PreparationAlreadyConsumedError,
)
from community_mcp.assistance.service import AssistanceService
from community_mcp.policy.assistance import AssistancePolicy
from community_mcp.schemas.assistance import AssistanceAction


async def prepare_response():
    request = await AssistanceService().get_public_context("HELP-2026-001")

    prepared = AssistancePolicy().prepare_response(
        request,
        actor_id="demo-member-001",
        action=AssistanceAction.DONATE_BLOOD,
    )

    store = AssistancePreparationStore()
    store.save(prepared)

    return prepared, store


@pytest.mark.asyncio
async def test_confirmed_response_creates_record_and_audit() -> None:
    prepared, store = await prepare_response()
    service = AssistanceActionService(store)

    result = service.confirm_response(
        prepared.preparation_id,
        actor_id="demo-member-001",
        confirmed=True,
    )

    assert result.response.public_reference == "HELP-2026-001"
    assert result.response.action == AssistanceAction.DONATE_BLOOD
    assert result.audit.event_type == "ASSISTANCE_RESPONSE_RECORDED"
    assert result.audit.actor_id == "demo-member-001"


@pytest.mark.asyncio
async def test_response_cannot_execute_without_confirmation() -> None:
    prepared, store = await prepare_response()
    service = AssistanceActionService(store)

    with pytest.raises(ConfirmationRequiredError):
        service.confirm_response(
            prepared.preparation_id,
            actor_id="demo-member-001",
            confirmed=False,
        )


@pytest.mark.asyncio
async def test_wrong_actor_cannot_confirm_response() -> None:
    prepared, store = await prepare_response()
    service = AssistanceActionService(store)

    with pytest.raises(ActorMismatchError):
        service.confirm_response(
            prepared.preparation_id,
            actor_id="different-member",
            confirmed=True,
        )


@pytest.mark.asyncio
async def test_preparation_cannot_be_replayed() -> None:
    prepared, store = await prepare_response()
    service = AssistanceActionService(store)

    service.confirm_response(
        prepared.preparation_id,
        actor_id="demo-member-001",
        confirmed=True,
    )

    with pytest.raises(PreparationAlreadyConsumedError):
        service.confirm_response(
            prepared.preparation_id,
            actor_id="demo-member-001",
            confirmed=True,
        )
