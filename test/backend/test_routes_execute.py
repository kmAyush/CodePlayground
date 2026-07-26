from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routes.execute import router
from backend.session import session_manager
from core.constants import REVERSE_BUILTIN_MAP


@pytest.fixture(autouse=True)
def clear_sessions():
    session_manager._sessions.clear()
    session_manager._timestamps.clear()
    yield
    session_manager._sessions.clear()
    session_manager._timestamps.clear()


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def make_session(reverse_map=None):
    session_id = session_manager.create()
    session_manager.update(session_id, reverse_map=reverse_map or dict(REVERSE_BUILTIN_MAP))
    return session_id


def test_execute_hindi_success_populates_both_panels(client):
    session_id = make_session()
    response = client.post(
        "/execute/hindi", json={"code": "छापो(2 + 3)", "session_id": session_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["hindi_output"] == "5\n"
    assert data["english_output"] == "5\n"
    assert data["hindi_error"] == ""
    assert data["success"] is True


def test_execute_hindi_name_error(client):
    session_id = make_session()
    response = client.post(
        "/execute/hindi",
        json={"code": "छापो(undefined_variable)", "session_id": session_id},
    )
    data = response.json()
    assert "पिछलावा" in data["hindi_error"]
    assert data["success"] is False


def test_execute_hindi_missing_session_returns_404(client):
    response = client.post(
        "/execute/hindi", json={"code": "छापो(1)", "session_id": "unknown-session"}
    )
    assert response.status_code == 404


def test_execute_hindi_timeout_mocked(client):
    session_id = make_session()
    with patch(
        "backend.routes.execute.execute_hindi_source",
        side_effect=TimeoutError("execution exceeded 5s"),
    ):
        response = client.post(
            "/execute/hindi", json={"code": "छापो(1)", "session_id": session_id}
        )
    data = response.json()
    assert "समयसीमा" in data["hindi_error"]
    assert data["success"] is False


def test_execute_english_success(client):
    response = client.post("/execute/english", json={"code": 'print("hello")'})
    assert response.status_code == 200
    data = response.json()
    assert data["output"] == "hello\n"
    assert data["error"] == ""
    assert data["success"] is True


def test_execute_english_syntax_error(client):
    response = client.post("/execute/english", json={"code": "def broken(:\n    pass"})
    data = response.json()
    assert data["output"] == ""
    assert data["error"] != ""
    assert data["success"] is False
