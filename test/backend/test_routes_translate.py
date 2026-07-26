import ast
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routes.translate import router
from backend.session import session_manager


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


FAKE_TRANSLATION = {"greet": "नमस्कार_करो", "name": "नाम"}


def test_to_hindi_valid_code_returns_hindi_code_and_session_id(client):
    with patch("core.main.translate_identifiers", return_value=FAKE_TRANSLATION):
        response = client.post(
            "/translate/to-hindi",
            json={"code": "def greet(name):\n    print(name)", "session_id": None},
        )
    assert response.status_code == 200
    data = response.json()
    assert "काम" in data["hindi_code"]
    assert data["session_id"]
    assert data["error"] == ""


def test_to_hindi_empty_code_returns_422(client):
    response = client.post("/translate/to-hindi", json={"code": "", "session_id": None})
    assert response.status_code == 422


def test_to_hindi_null_session_id_creates_new_session(client):
    with patch("core.main.translate_identifiers", return_value={}):
        response = client.post(
            "/translate/to-hindi", json={"code": "x = 1", "session_id": None}
        )
    data = response.json()
    assert session_manager.get(data["session_id"]) is not None


def test_to_english_valid_returns_parseable_python(client):
    with patch("core.main.translate_identifiers", return_value=FAKE_TRANSLATION):
        to_hindi_response = client.post(
            "/translate/to-hindi",
            json={"code": "def greet(name):\n    print(name)", "session_id": None},
        )
    session_id = to_hindi_response.json()["session_id"]
    hindi_code = to_hindi_response.json()["hindi_code"]

    response = client.post(
        "/translate/to-english", json={"code": hindi_code, "session_id": session_id}
    )
    assert response.status_code == 200
    english_code = response.json()["english_code"]
    ast.parse(english_code)  # raises SyntaxError if not valid Python


def test_to_english_missing_session_id_returns_422(client):
    response = client.post("/translate/to-english", json={"code": "काम greet():\n    पास"})
    assert response.status_code == 422


def test_to_english_unknown_session_id_returns_404(client):
    response = client.post(
        "/translate/to-english",
        json={"code": "काम greet():\n    पास", "session_id": "unknown-session"},
    )
    assert response.status_code == 404


def test_roundtrip_to_hindi_then_to_english(client):
    original = "def greet(name):\n    print(name)"
    with patch("core.main.translate_identifiers", return_value=FAKE_TRANSLATION):
        to_hindi_response = client.post(
            "/translate/to-hindi", json={"code": original, "session_id": None}
        )
    session_id = to_hindi_response.json()["session_id"]
    hindi_code = to_hindi_response.json()["hindi_code"]

    to_english_response = client.post(
        "/translate/to-english", json={"code": hindi_code, "session_id": session_id}
    )
    english_code = to_english_response.json()["english_code"]

    assert ast.dump(ast.parse(original)) == ast.dump(ast.parse(english_code))
