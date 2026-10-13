from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class SimulatorSession:
    event_slug: str | None = None
    assistance_reference: str | None = None
    updated_at: float = 0.0


class SimulatorSessionStore:
    """Temporary public conversation context for the read-only simulator."""

    def __init__(
        self,
        *,
        ttl_seconds: int = 1800,
        max_sessions: int = 1000,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions
        self._sessions: dict[str, SimulatorSession] = {}

    def _get(self, session_id: str) -> SimulatorSession | None:
        now = time.monotonic()
        session = self._sessions.get(session_id)

        if session is None:
            return None

        if now - session.updated_at > self.ttl_seconds:
            del self._sessions[session_id]
            return None

        session.updated_at = now
        return session

    def _remember(self, session_id: str) -> SimulatorSession:
        existing = self._get(session_id)

        if existing is not None:
            return existing

        now = time.monotonic()

        expired = [
            key
            for key, value in self._sessions.items()
            if now - value.updated_at > self.ttl_seconds
        ]

        for key in expired:
            del self._sessions[key]

        if len(self._sessions) >= self.max_sessions:
            oldest = min(
                self._sessions,
                key=lambda key: self._sessions[key].updated_at,
            )
            del self._sessions[oldest]

        session = SimulatorSession(updated_at=now)
        self._sessions[session_id] = session
        return session

    def has_event_context(self, session_id: str) -> bool:
        session = self._get(session_id)
        return session is not None and session.event_slug is not None

    def remember_event(self, session_id: str, event_slug: str) -> None:
        self._remember(session_id).event_slug = event_slug

    def get_assistance_reference(self, session_id: str) -> str | None:
        session = self._get(session_id)
        return session.assistance_reference if session else None

    def remember_assistance(self, session_id: str, reference: str) -> None:
        self._remember(session_id).assistance_reference = reference
