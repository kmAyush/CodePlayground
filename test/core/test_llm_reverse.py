import json
import re
from unittest.mock import MagicMock, patch

import pytest
from sarvamai.core.api_error import ApiError

from core.llm_reverse import reverse_translate_identifiers


def make_response(content, finish_reason="stop"):
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content
    response.choices[0].finish_reason = finish_reason
    return response


def test_empty_list_returns_empty_dict_without_api_call():
    with patch("core.llm_reverse.client") as mock_client:
        result = reverse_translate_identifiers([])
        assert result == {}
        mock_client.chat.completions.assert_not_called()


def test_valid_hindi_identifiers_all_keys_present():
    with patch("core.llm_reverse.client") as mock_client:
        mock_client.chat.completions.return_value = make_response(
            json.dumps({"जोड़": "add", "छात्र": "student"}, ensure_ascii=False)
        )
        result = reverse_translate_identifiers(["जोड़", "छात्र"])
        assert result == {"जोड़": "add", "छात्र": "student"}


def test_output_values_are_valid_python_identifiers():
    with patch("core.llm_reverse.client") as mock_client:
        mock_client.chat.completions.return_value = make_response(
            json.dumps({"जोड़": "add", "छात्र": "student"}, ensure_ascii=False)
        )
        result = reverse_translate_identifiers(["जोड़", "छात्र"])
        for value in result.values():
            assert re.match(r"^[a-zA-Z_]\w*$", value)


def test_missing_key_falls_back_to_original_hindi():
    with patch("core.llm_reverse.client") as mock_client:
        mock_client.chat.completions.return_value = make_response(
            json.dumps({"जोड़": "add"}, ensure_ascii=False)
        )
        result = reverse_translate_identifiers(["जोड़", "अ"])
        assert result["जोड़"] == "add"
        assert result["अ"] == "अ"


def test_finish_reason_length_raises_runtime_error():
    with patch("core.llm_reverse.client") as mock_client:
        mock_client.chat.completions.return_value = make_response(
            content='{"जोड़":"add"}', finish_reason="length"
        )
        with pytest.raises(RuntimeError):
            reverse_translate_identifiers(["जोड़"])


def test_empty_content_raises_runtime_error():
    with patch("core.llm_reverse.client") as mock_client:
        mock_client.chat.completions.return_value = make_response(content="")
        with pytest.raises(RuntimeError):
            reverse_translate_identifiers(["जोड़"])


def test_invalid_json_raises_runtime_error_with_preview():
    with patch("core.llm_reverse.client") as mock_client:
        mock_client.chat.completions.return_value = make_response(content="not json")
        with pytest.raises(RuntimeError, match="not json"):
            reverse_translate_identifiers(["जोड़"])


def test_api_429_raises_runtime_error_with_rate_limit_message():
    with patch("core.llm_reverse.client") as mock_client:
        mock_client.chat.completions.side_effect = ApiError(
            status_code=429, body={"error": "too many requests"}
        )
        with pytest.raises(RuntimeError, match="Rate limit"):
            reverse_translate_identifiers(["जोड़"])
