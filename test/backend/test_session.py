import time
import uuid

from backend.session import SessionManager


def test_create_returns_valid_uuid_string():
    manager = SessionManager()
    session_id = manager.create()
    assert isinstance(session_id, str)
    uuid.UUID(session_id)  # raises ValueError if not a valid UUID


def test_get_after_create_returns_empty_dict():
    manager = SessionManager()
    session_id = manager.create()
    assert manager.get(session_id) == {}


def test_update_merges_data_correctly():
    manager = SessionManager()
    session_id = manager.create()
    manager.update(session_id, hindi_source="काम")
    manager.update(session_id, english_source="def")
    data = manager.get(session_id)
    assert data == {"hindi_source": "काम", "english_source": "def"}


def test_get_nonexistent_session_returns_none():
    manager = SessionManager()
    assert manager.get("does-not-exist") is None


def test_delete_removes_session():
    manager = SessionManager()
    session_id = manager.create()
    manager.delete(session_id)
    assert manager.get(session_id) is None


def test_two_sessions_are_independent():
    manager = SessionManager()
    session_a = manager.create()
    session_b = manager.create()
    manager.update(session_a, hindi_source="अ")
    assert manager.get(session_a) == {"hindi_source": "अ"}
    assert manager.get(session_b) == {}


def test_cleanup_expired_removes_old_sessions():
    manager = SessionManager()
    session_id = manager.create()
    manager._timestamps[session_id] -= 100
    manager.cleanup_expired(max_age_seconds=10)
    assert manager.get(session_id) is None


def test_cleanup_expired_keeps_recent_sessions():
    manager = SessionManager()
    session_id = manager.create()
    manager.cleanup_expired(max_age_seconds=3600)
    assert manager.get(session_id) == {}
