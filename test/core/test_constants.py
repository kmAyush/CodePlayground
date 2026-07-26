from core.constants import (
    BUILTIN_MAP,
    BUILTIN_NAMES,
    DUNDER,
    ERROR_MSG_MAP,
    KEYWORD_MAP,
    REVERSE_BUILTIN_MAP,
)


def test_builtin_names_matches_builtin_map_keys():
    assert BUILTIN_NAMES == set(BUILTIN_MAP.keys())


def test_reverse_builtin_map_is_exact_inverse():
    assert REVERSE_BUILTIN_MAP == {v: k for k, v in BUILTIN_MAP.items()}
    for english, hindi in BUILTIN_MAP.items():
        assert REVERSE_BUILTIN_MAP[hindi] == english


def test_no_key_overlap_between_keyword_and_builtin_maps():
    assert set(KEYWORD_MAP.keys()).isdisjoint(set(BUILTIN_MAP.keys()))


def test_error_msg_map_sorted_longest_first():
    lengths = [len(fragment) for fragment, _ in ERROR_MSG_MAP]
    assert lengths == sorted(lengths, reverse=True)


def test_dunder_true_for_init():
    assert DUNDER("__init__") is True


def test_dunder_false_for_plain_name():
    assert DUNDER("greet") is False
