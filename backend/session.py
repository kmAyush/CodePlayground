"""Store and retrieve session data in memory.

One session per browser tab, identified by a session_id (UUID).
"""

import time
import uuid


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, dict] = {}
        self._timestamps: dict[str, float] = {}

    def create(self) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {}
        self._timestamps[session_id] = time.monotonic()
        return session_id

    def get(self, session_id: str) -> dict | None:
        return self._sessions.get(session_id)

    def update(self, session_id: str, **kwargs) -> None:
        if session_id not in self._sessions:
            raise KeyError(f"Unknown session_id: {session_id}")
        self._sessions[session_id].update(kwargs)
        self._timestamps[session_id] = time.monotonic()

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        self._timestamps.pop(session_id, None)

    def cleanup_expired(self, max_age_seconds: float) -> None:
        now = time.monotonic()
        expired = [
            session_id
            for session_id, updated_at in self._timestamps.items()
            if now - updated_at > max_age_seconds
        ]
        for session_id in expired:
            self.delete(session_id)


# Shared instance used by the route modules to keep session state consistent
# across requests within a running app.
session_manager = SessionManager()
