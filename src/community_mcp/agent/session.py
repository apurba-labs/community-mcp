from dataclasses import dataclass
from uuid import UUID

from community_mcp.agent.schemas import SupportedLocale


class SessionNotFoundError(Exception):
    """Raised when an agent session does not exist."""


class SessionActorMismatchError(Exception):
    """Raised when a session is reused by another actor."""


@dataclass
class AgentSession:
    session_id: str
    locale: SupportedLocale
    actor_id: str | None = None
    current_event_slug: str | None = None
    current_assistance_reference: str | None = None
    pending_preparation_id: UUID | None = None


class AgentSessionStore:
    """In-memory conversation state for the hackathon agent journey."""

    def __init__(self) -> None:
        self._sessions: dict[str, AgentSession] = {}

    def get_or_create(
        self,
        *,
        session_id: str,
        locale: SupportedLocale,
        actor_id: str | None = None,
    ) -> AgentSession:
        session = self._sessions.get(session_id)

        if session is None:
            session = AgentSession(
                session_id=session_id,
                locale=locale,
                actor_id=actor_id,
            )
            self._sessions[session_id] = session
            return session

        if (
            session.actor_id is not None
            and actor_id is not None
            and session.actor_id != actor_id
        ):
            raise SessionActorMismatchError(
                f"Session {session_id!r} belongs to another actor."
            )

        if session.actor_id is None and actor_id is not None:
            session.actor_id = actor_id

        session.locale = locale
        return session

    def get(self, session_id: str) -> AgentSession:
        session = self._sessions.get(session_id)

        if session is None:
            raise SessionNotFoundError(
                f"Session {session_id!r} does not exist."
            )

        return session

    def set_event_context(
        self,
        session_id: str,
        event_slug: str,
    ) -> None:
        self.get(session_id).current_event_slug = event_slug

    def set_assistance_context(
        self,
        session_id: str,
        public_reference: str,
    ) -> None:
        self.get(
            session_id
        ).current_assistance_reference = public_reference

    def set_pending_preparation(
        self,
        session_id: str,
        preparation_id: UUID,
    ) -> None:
        self.get(
            session_id
        ).pending_preparation_id = preparation_id

    def clear_pending_preparation(
        self,
        session_id: str,
    ) -> None:
        self.get(session_id).pending_preparation_id = None
