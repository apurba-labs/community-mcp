import sqlite3

import pytest

from community_mcp.assistance.action_service import (
    ActorMismatchError,
    ConfirmationRequiredError,
)
from community_mcp.assistance.preparation_store import (
    PreparationAlreadyConsumedError,
)
from community_mcp.assistance.service import AssistanceService
from community_mcp.assistance.sqlite_store import SQLiteAssistanceStore
from community_mcp.policy.assistance import AssistancePolicy
from community_mcp.schemas.assistance import AssistanceAction


async def make_preparation():
    request = await AssistanceService().get_public_context("HELP-2026-001")

    return AssistancePolicy().prepare_response(
        request,
        actor_id="demo-member-001",
        action=AssistanceAction.DONATE_BLOOD,
    )


@pytest.mark.asyncio
async def test_preparation_survives_restart(tmp_path):
    database = tmp_path / "assistance.sqlite"
    prepared = await make_preparation()

    SQLiteAssistanceStore(database).save(prepared)

    restarted = SQLiteAssistanceStore(database)
    restored = restarted.get(prepared.preparation_id)

    assert restored == prepared


@pytest.mark.asyncio
async def test_confirmation_and_audit_survive_restart(tmp_path):
    database = tmp_path / "assistance.sqlite"
    prepared = await make_preparation()

    store = SQLiteAssistanceStore(database)
    store.save(prepared)

    confirmed = store.confirm_response(
        prepared.preparation_id,
        actor_id="demo-member-001",
        confirmed=True,
    )

    restarted = SQLiteAssistanceStore(database)
    restored = restarted.get_confirmed_response(prepared.preparation_id)

    assert restored == confirmed
    assert restored.audit.event_type == "ASSISTANCE_RESPONSE_RECORDED"

    with pytest.raises(PreparationAlreadyConsumedError):
        restarted.confirm_response(
            prepared.preparation_id,
            actor_id="demo-member-001",
            confirmed=True,
        )


@pytest.mark.asyncio
async def test_confirmation_requires_explicit_consent(tmp_path):
    store = SQLiteAssistanceStore(tmp_path / "assistance.sqlite")
    prepared = await make_preparation()
    store.save(prepared)

    with pytest.raises(ConfirmationRequiredError):
        store.confirm_response(
            prepared.preparation_id,
            actor_id="demo-member-001",
            confirmed=False,
        )

    assert store.get(prepared.preparation_id) == prepared


@pytest.mark.asyncio
async def test_wrong_actor_does_not_consume_preparation(tmp_path):
    store = SQLiteAssistanceStore(tmp_path / "assistance.sqlite")
    prepared = await make_preparation()
    store.save(prepared)

    with pytest.raises(ActorMismatchError):
        store.confirm_response(
            prepared.preparation_id,
            actor_id="another-member",
            confirmed=True,
        )

    assert store.get(prepared.preparation_id) == prepared


@pytest.mark.asyncio
async def test_failed_audit_insert_rolls_back_entire_confirmation(tmp_path):
    database = tmp_path / "assistance.sqlite"
    store = SQLiteAssistanceStore(database)
    prepared = await make_preparation()
    store.save(prepared)

    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TRIGGER reject_audit
            BEFORE INSERT ON audit_receipts
            BEGIN
                SELECT RAISE(ABORT, 'audit unavailable');
            END;
            """
        )

    with pytest.raises(sqlite3.IntegrityError):
        store.confirm_response(
            prepared.preparation_id,
            actor_id="demo-member-001",
            confirmed=True,
        )

    assert store.get(prepared.preparation_id) == prepared
    assert store.get_confirmed_response(prepared.preparation_id) is None

    with sqlite3.connect(database) as connection:
        response_count = connection.execute(
            "SELECT COUNT(*) FROM responses"
        ).fetchone()[0]

    assert response_count == 0
