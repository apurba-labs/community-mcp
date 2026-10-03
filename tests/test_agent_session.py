from uuid import uuid4

import pytest

from community_mcp.agent.schemas import SupportedLocale
from community_mcp.agent.session import (
    AgentSessionStore,
    SessionActorMismatchError,
    SessionNotFoundError,
)


def test_creates_agent_session() -> None:
    store = AgentSessionStore()

    session = store.get_or_create(
        session_id="session-001",
        locale=SupportedLocale.EN,
        actor_id="demo-member-001",
    )

    assert session.session_id == "session-001"
    assert session.locale == SupportedLocale.EN
    assert session.actor_id == "demo-member-001"
    assert session.pending_preparation_id is None


def test_same_session_can_continue_in_bangla() -> None:
    store = AgentSessionStore()

    store.get_or_create(
        session_id="session-001",
        locale=SupportedLocale.EN,
        actor_id="demo-member-001",
    )

    session = store.get_or_create(
        session_id="session-001",
        locale=SupportedLocale.BN,
        actor_id="demo-member-001",
    )

    assert session.locale == SupportedLocale.BN
    assert session.actor_id == "demo-member-001"


def test_session_remembers_event_and_assistance_context() -> None:
    store = AgentSessionStore()

    store.get_or_create(
        session_id="session-001",
        locale=SupportedLocale.EN,
        actor_id="demo-member-001",
    )

    store.set_event_context(
        "session-001",
        "centenary-celebration",
    )
    store.set_assistance_context(
        "session-001",
        "HELP-2026-001",
    )

    session = store.get("session-001")

    assert session.current_event_slug == "centenary-celebration"
    assert (
        session.current_assistance_reference
        == "HELP-2026-001"
    )


def test_session_remembers_and_clears_pending_preparation() -> None:
    store = AgentSessionStore()

    store.get_or_create(
        session_id="session-001",
        locale=SupportedLocale.EN,
        actor_id="demo-member-001",
    )

    preparation_id = uuid4()

    store.set_pending_preparation(
        "session-001",
        preparation_id,
    )

    assert (
        store.get("session-001").pending_preparation_id
        == preparation_id
    )

    store.clear_pending_preparation("session-001")

    assert (
        store.get("session-001").pending_preparation_id
        is None
    )


def test_session_cannot_be_reused_by_different_actor() -> None:
    store = AgentSessionStore()

    store.get_or_create(
        session_id="session-001",
        locale=SupportedLocale.EN,
        actor_id="demo-member-001",
    )

    with pytest.raises(SessionActorMismatchError):
        store.get_or_create(
            session_id="session-001",
            locale=SupportedLocale.EN,
            actor_id="demo-member-002",
        )


def test_unknown_session_is_rejected() -> None:
    store = AgentSessionStore()

    with pytest.raises(SessionNotFoundError):
        store.get("missing-session")
