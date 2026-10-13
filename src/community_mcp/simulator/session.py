from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class SimulatorSession:
    event_slug: str
    updated_at: float


class SimulatorSessionStore:
    """Temporary event context for the read-only simulator."""

    def __init__(
        self,
        *,
        ttl_seconds: int = 1800,
        max_sessions: int = 1000,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions
        self._sessions: dict[str, SimulatorSession] = {}

    def has_event_context(self, session_id: str) -> bool:
        now = time.monotonic()
        session = self._sessions.get(session_id)

        if session is None:
            return False

        if now - session.updated_at > self.ttl_seconds:
            del self._sessions[session_id]
            return False

        session.updated_at = now
        return True

    def remember_event(self, session_id: str, event_slug: str) -> None:
        now = time.monotonic()

        expired = [
            key
            for key, value in self._sessions.items()
            if now - value.updated_at > self.ttl_seconds
        ]

        for key in expired:
            del self._sessions[key]

        if session_id not in self._sessions and len(self._sessions) >= self.max_sessions:
            oldest = min(
                self._sessions,
                key=lambda key: self._sessions[key].updated_at,
            )
            del self._sessions[oldest]

        self._sessions[session_id] = SimulatorSession(
            event_slug=event_slug,
            updated_at=now,
        )
