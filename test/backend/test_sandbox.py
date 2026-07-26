import backend.sandbox as sandbox_module
from backend.sandbox import run_in_sandbox


def test_simple_print():
    stdout, stderr = run_in_sandbox('print("hello")')
    assert stdout == "hello\n"
    assert stderr == ""


def test_arithmetic():
    stdout, stderr = run_in_sandbox("print(2 + 3)")
    assert stdout == "5\n"
    assert stderr == ""


def test_timeout_returns_error_and_empty_stdout():
    stdout, stderr = run_in_sandbox(
        "import time; time.sleep(2)", timeout_seconds=1
    )
    assert stdout == ""
    assert "TimeoutError" in stderr


def test_infinite_loop_caught_by_timeout():
    stdout, stderr = run_in_sandbox("while True:\n    pass", timeout_seconds=1)
    assert stdout == ""
    assert "TimeoutError" in stderr


def test_syntax_error_in_source():
    stdout, stderr = run_in_sandbox("def broken(:\n    pass")
    assert stdout == ""
    assert "SyntaxError" in stderr


def test_name_error():
    stdout, stderr = run_in_sandbox("print(undefined_variable)")
    assert "NameError" in stderr


def test_sandbox_module_does_not_import_project_modules():
    assert "core" not in vars(sandbox_module)
    assert not hasattr(sandbox_module, "execute_hindi_source")
