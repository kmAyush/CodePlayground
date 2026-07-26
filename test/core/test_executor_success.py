import sys
import textwrap

from core.constants import REVERSE_BUILTIN_MAP
from core.executor import execute_hindi_source


def run(source: str, extra_reverse_map: dict | None = None):
    reverse_map = {**REVERSE_BUILTIN_MAP, **(extra_reverse_map or {})}
    return execute_hindi_source(textwrap.dedent(source).strip(), reverse_map)


def test_hello_world():
    stdout, error = run('छापो("नमस्ते दुनिया")')
    assert stdout == "नमस्ते दुनिया\n"
    assert error == ""


def test_arithmetic():
    stdout, error = run("छापो(2 + 3)")
    assert stdout == "5\n"
    assert error == ""


def test_function_def_and_call():
    stdout, error = run(
        """
        काम जोड़(a, b):
            वापस a + b

        छापो(जोड़(2, 3))
        """,
        extra_reverse_map={"जोड़": "add"},
    )
    assert stdout == "5\n"
    assert error == ""


def test_class_instantiation_and_method_call():
    stdout, error = run(
        """
        क्लास Animal:
            काम __init__(स्वयं, name):
                स्वयं.name = name

            काम speak(स्वयं):
                छापो(स्वयं.name)

        a = Animal("Rex")
        a.speak()
        """
    )
    assert stdout == "Rex\n"
    assert error == ""


def test_for_loop_output():
    stdout, error = run(
        """
        केलिए i में श्रेणी(3):
            छापो(i)
        """
    )
    assert stdout == "0\n1\n2\n"
    assert error == ""


def test_while_loop_with_break():
    stdout, error = run(
        """
        i = 0
        जबतक True:
            अगर i == 3:
                रुको
            छापो(i)
            i = i + 1
        """
    )
    assert stdout == "0\n1\n2\n"
    assert error == ""


def test_try_except_catches_error():
    stdout, error = run(
        """
        कोशिश:
            x = 1 / 0
        सिवाय ZeroDivisionError:
            छापो("caught")
        """
    )
    assert stdout == "caught\n"
    assert error == ""


def test_name_main_guard_executes_main():
    stdout, error = run(
        """
        काम main():
            छापो("hi")

        अगर __name__ == '__main__':
            main()
        """
    )
    assert stdout == "hi\n"
    assert error == ""


def test_true_false_none_translated_in_output():
    stdout, error = run("छापो(True, False, None)")
    assert stdout == "सच झूठ कुछनहीं\n"
    assert error == ""


def test_stdout_restored_after_error():
    original_stdout = sys.stdout
    stdout, error = run("छापो(undefined_variable)")
    assert error != ""
    assert sys.stdout is original_stdout
