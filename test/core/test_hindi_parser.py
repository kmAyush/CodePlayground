import textwrap

from core.hindi_parser import extract_hindi_identifiers


def extract(source: str) -> dict:
    return extract_hindi_identifiers(textwrap.dedent(source).strip())


def test_basic_hindi_function_extracts_name_and_parameters():
    result = extract(
        """
        काम जोड़(a, b):
            वापस a + b
        """
    )
    assert "जोड़" in result["by_category"]["functions"]
    assert "a" in result["by_category"]["parameters"]
    assert "b" in result["by_category"]["parameters"]


def test_skips_known_hindi_builtins():
    result = extract(
        """
        छापो(योग([1, 2]))
        x = श्रेणी(5)
        """
    )
    assert "छापो" not in result["flat_unique"]
    assert "योग" not in result["flat_unique"]
    assert "श्रेणी" not in result["flat_unique"]
    assert "x" in result["flat_unique"]


def test_skips_swayam():
    result = extract(
        """
        क्लास Animal:
            काम बोलो(स्वयं):
                छापो(स्वयं.name)
        """
    )
    assert "स्वयं" not in result["flat_unique"]


def test_skips_dunders():
    result = extract(
        """
        क्लास Foo:
            काम __init__(स्वयं):
                पास
        """
    )
    assert "__init__" not in result["flat_unique"]


def test_returns_same_dict_structure_as_parser():
    result = extract("x = 1")
    assert set(result.keys()) == {"by_category", "flat_unique"}
    assert set(result["by_category"].keys()) == {
        "functions",
        "classes",
        "variables",
        "parameters",
        "attributes",
        "calls",
    }
