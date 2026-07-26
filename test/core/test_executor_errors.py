import textwrap

from core.constants import REVERSE_BUILTIN_MAP
from core.executor import execute_hindi_source


def run(source: str, extra_reverse_map: dict | None = None):
    reverse_map = {**REVERSE_BUILTIN_MAP, **(extra_reverse_map or {})}
    return execute_hindi_source(textwrap.dedent(source).strip(), reverse_map)


def test_name_error():
    stdout, error = run("छापो(undefined_variable)")
    assert "पिछलावा" in error
    assert "नाम_त्रुटि" in error
    assert "परिभाषित नहीं है" in error


def test_type_error_wrong_args():
    stdout, error = run(
        """
        काम greet(name):
            छापो(name)

        greet(1, 2)
        """
    )
    assert "प्रकार_त्रुटि" in error
    assert "स्थितिगत तर्क" in error


def test_type_error_str_plus_int():
    stdout, error = run('छापो("5" + 5)')
    assert "स्ट्रिंग" in error


def test_zero_division_error():
    stdout, error = run("छापो(1 / 0)")
    assert "शून्य_भाग_त्रुटि" in error
    assert "शून्य से भाग" in error


def test_index_error():
    stdout, error = run(
        """
        x = [1, 2, 3]
        छापो(x[10])
        """
    )
    assert "अनुक्रमणिका_त्रुटि" in error


def test_key_error():
    stdout, error = run(
        """
        x = {"a": 1}
        छापो(x["b"])
        """
    )
    assert "कुंजी_त्रुटि" in error


def test_attribute_error():
    stdout, error = run(
        """
        x = 5
        छापो(x.missing_attr)
        """
    )
    assert "विशेषता_त्रुटि" in error


def test_recursion_error():
    stdout, error = run(
        """
        काम recurse():
            वापस recurse()

        recurse()
        """
    )
    assert "पुनरावर्तन_त्रुटि" in error


def test_multi_frame_all_user_frames_present_executor_absent():
    stdout, error = run(
        """
        काम inner():
            वापस 1 / 0

        काम outer():
            वापस inner()

        outer()
        """
    )
    assert "executor.py" not in error
    assert error.count("फ़ाइल") >= 2


def test_traceback_english_word_absent():
    stdout, error = run("छापो(undefined_variable)")
    assert "Traceback" not in error


def test_most_recent_call_last_english_absent():
    stdout, error = run("छापो(undefined_variable)")
    assert "most recent call last" not in error
