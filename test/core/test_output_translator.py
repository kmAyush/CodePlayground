from core.constants import ERROR_TYPE_MAP
from core.output_translator import (
    translate_error,
    translate_frame_line,
    translate_message,
    translate_output,
    translate_type,
)


def test_translate_output_true_as_whole_word():
    assert translate_output("True") == "सच"


def test_translate_output_does_not_match_substring():
    assert translate_output("TrueValue") == "TrueValue"


def test_translate_output_list_of_values():
    assert translate_output("[True, False, None]") == "[सच, झूठ, कुछनहीं]"


def test_translate_type_all_35_entries():
    for english, hindi in ERROR_TYPE_MAP.items():
        assert translate_type(english) == hindi
    assert len(ERROR_TYPE_MAP) == 35


def test_translate_type_unknown_returns_unchanged():
    assert translate_type("SomeUnknownError") == "SomeUnknownError"


def test_translate_message_name_not_defined():
    assert translate_message("name 'myVar' is not defined") == "नाम 'myVar' परिभाषित नहीं है"


def test_translate_message_preserves_hindi_var_name():
    assert (
        translate_message("name 'अपरिभाषित' is not defined")
        == "नाम 'अपरिभाषित' परिभाषित नहीं है"
    )


def test_translate_frame_line():
    line = '  File "x", line 3, in foo'
    assert translate_frame_line(line) == '  फ़ाइल "x", पंक्ति 3, में foo'


def test_translate_error_contains_traceback_word_not_english():
    error_str = (
        "Traceback (most recent call last):\n"
        '  File "<hindi>", line 1, in <module>\n'
        "    वापस 1 / 0\n"
        "ZeroDivisionError: division by zero"
    )
    result = translate_error(error_str)
    assert "पिछलावा" in result
    assert "Traceback" not in result


def test_translate_error_empty_string_returns_empty():
    assert translate_error("") == ""
