from core.parser import extract_identifiers


def test_basic_function_extracts_name_and_parameters():
    result = extract_identifiers(
        """
        def greet(name):
            print(name)
        """
    )
    assert "greet" in result["by_category"]["functions"]
    assert "name" in result["by_category"]["parameters"]


def test_class_extracts_name_and_methods_self_excluded():
    result = extract_identifiers(
        """
        class Animal:
            def speak(self, sound):
                self.sound = sound
        """
    )
    assert "Animal" in result["by_category"]["classes"]
    assert "speak" in result["by_category"]["functions"]
    assert "self" not in result["flat_unique"]


def test_dict_and_for_extracts_variables_not_string_keys():
    result = extract_identifiers(
        """
        d = {"a": 1, "b": 2}
        for key in d:
            print(key)
        """
    )
    assert "d" in result["by_category"]["variables"]
    assert "key" in result["by_category"]["variables"]
    assert "a" not in result["flat_unique"]
    assert "b" not in result["flat_unique"]


def test_name_main_guard_excluded():
    result = extract_identifiers(
        """
        def main():
            pass

        if __name__ == "__main__":
            main()
        """
    )
    assert "__name__" not in result["flat_unique"]
    assert "__main__" not in result["flat_unique"]


def test_builtins_excluded():
    result = extract_identifiers(
        """
        for i in range(len("hello")):
            print(i)
        """
    )
    assert "print" not in result["flat_unique"]
    assert "len" not in result["flat_unique"]
    assert "range" not in result["flat_unique"]


def test_attributes_extracted_from_self():
    result = extract_identifiers(
        """
        class Animal:
            def __init__(self, name, sound):
                self.name = name
                self.sound = sound
        """
    )
    assert "name" in result["by_category"]["attributes"]
    assert "sound" in result["by_category"]["attributes"]


def test_deduplication_across_categories():
    result = extract_identifiers(
        """
        def greet():
            pass

        greet()
        """
    )
    assert result["flat_unique"].count("greet") == 1
    assert "greet" in result["by_category"]["functions"]
    assert "greet" in result["by_category"]["calls"]


def test_empty_source_returns_empty_result():
    result = extract_identifiers("")
    assert result["flat_unique"] == []
    assert all(items == [] for items in result["by_category"].values())


def test_dedent_handles_indented_triple_quoted_source():
    result = extract_identifiers(
        """
        def greet(name):
            print(name)
        """
    )
    assert "greet" in result["by_category"]["functions"]


def test_flat_unique_sorted_alphabetically():
    result = extract_identifiers(
        """
        def zebra():
            pass

        def apple():
            pass
        """
    )
    functions_only = [n for n in result["flat_unique"] if n in ("zebra", "apple")]
    assert functions_only == sorted(functions_only)
