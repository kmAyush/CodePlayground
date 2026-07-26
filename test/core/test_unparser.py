import ast
import textwrap

from core.constants import BUILTIN_MAP
from core.unparser import HindiUnparser


def render(source: str, name_map: dict | None = None) -> str:
    source = textwrap.dedent(source).strip()
    tree = ast.parse(source)
    unparser = HindiUnparser(name_map if name_map is not None else dict(BUILTIN_MAP))
    unparser.visit(tree)
    return unparser.render()


def test_hello_world():
    assert render('print("Hello")') == "छापो('Hello')"


def test_if_elif_else_uses_flat_elif_not_nested_if():
    output = render(
        """
        if x:
            pass
        elif y:
            pass
        else:
            pass
        """
    )
    lines = output.splitlines()
    assert any(line.strip().startswith("nahitoh") for line in lines)
    assert sum(1 for line in lines if line.strip().startswith("अगर ")) == 1
    assert any(line.strip() == "varna:" for line in lines)


def test_for_loop_emits_keliye_and_mein():
    output = render("for x in range(5):\n    pass")
    assert "केलिए" in output
    assert "में" in output


def test_function_def_emits_kaam_and_self_to_swayam():
    output = render(
        """
        class Animal:
            def speak(self, sound):
                pass
        """
    )
    assert "काम" in output
    assert "स्वयं" in output


def test_class_emits_klass():
    output = render("class Animal:\n    pass")
    assert "क्लास" in output


def test_try_except_finally_emitted():
    output = render(
        """
        try:
            pass
        except Exception:
            pass
        finally:
            pass
        """
    )
    assert "कोशिश" in output
    assert "सिवाय" in output
    assert "अंत_में" in output


def test_constant_strings_never_translated():
    output = render('x = "Hello"')
    assert "Hello" in output


def test_dunder_preserved():
    output = render(
        """
        class Foo:
            def __init__(self):
                pass
        """
    )
    assert "__init__" in output


def test_name_main_guard_emitted_correctly():
    output = render("if __name__ == '__main__':\n    pass")
    assert output == "अगर __name__ == '__main__':\n    पास"


def test_list_comprehension():
    output = render("[x for x in range(5)]")
    assert output == "[x केलिए x में श्रेणी(5)]"


def test_lambda():
    output = render("f = lambda x: x * 2")
    assert output == "f = लैम्ब्डा x: x * 2"


def test_indentation_is_four_spaces_per_level():
    output = render(
        """
        def foo():
            if True:
                pass
        """
    )
    lines = output.splitlines()
    assert lines[1].startswith("    ") and not lines[1].startswith("        ")
    assert lines[2].startswith("        ")
