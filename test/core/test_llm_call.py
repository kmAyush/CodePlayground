import json
from unittest.mock import MagicMock, patch

import pytest
from sarvamai.core.api_error import ApiError

from core.llm_call import translate_identifiers


def make_response(content, finish_reason="stop"):
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content
    response.choices[0].finish_reason = finish_reason
    return response


def test_empty_list_returns_empty_dict_without_api_call():
    with patch("core.llm_call.client") as mock_client:
        result = translate_identifiers([])
        assert result == {}
        mock_client.chat.completions.assert_not_called()


def test_valid_identifiers_returns_dict_with_all_keys():
    with patch("core.llm_call.client") as mock_client:
        mock_client.chat.completions.return_value = make_response(
            json.dumps({"greet": "स्वागत", "message": "संदेश"}, ensure_ascii=False)
        )
        result = translate_identifiers(["greet", "message"])
        assert result == {"greet": "स्वागत", "message": "संदेश"}


def test_missing_key_falls_back_to_original():
    with patch("core.llm_call.client") as mock_client:
        mock_client.chat.completions.return_value = make_response(
            json.dumps({"greet": "स्वागत"}, ensure_ascii=False)
        )
        result = translate_identifiers(["greet", "name"])
        assert result["greet"] == "स्वागत"
        assert result["name"] == "name"


def test_finish_reason_length_raises_runtime_error():
    with patch("core.llm_call.client") as mock_client:
        mock_client.chat.completions.return_value = make_response(
            content='{"greet":"स्वागत"}', finish_reason="length"
        )
        with pytest.raises(RuntimeError):
            translate_identifiers(["greet"])


def test_empty_content_raises_runtime_error():
    with patch("core.llm_call.client") as mock_client:
        mock_client.chat.completions.return_value = make_response(content="")
        with pytest.raises(RuntimeError):
            translate_identifiers(["greet"])


def test_invalid_json_raises_runtime_error_with_preview():
    with patch("core.llm_call.client") as mock_client:
        mock_client.chat.completions.return_value = make_response(
            content="not json at all"
        )
        with pytest.raises(RuntimeError, match="not json at all"):
            translate_identifiers(["greet"])


def test_api_429_raises_runtime_error_with_rate_limit_message():
    with patch("core.llm_call.client") as mock_client:
        mock_client.chat.completions.side_effect = ApiError(
            status_code=429, body={"error": "too many requests"}
        )
        with pytest.raises(RuntimeError, match="Rate limit"):
            translate_identifiers(["greet"])
