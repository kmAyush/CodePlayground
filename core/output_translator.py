"""Translate Python's English output tokens and traceback text to Hindi.

Never modifies user string values.
"""

import re

from core.constants import ERROR_MSG_MAP, ERROR_TYPE_MAP, OUTPUT_MAP, TRACEBACK_WORD

_WORD_PATTERN_CACHE: dict[str, re.Pattern] = {}


_BOUNDARY = "a-zA-Zऀ-ॿ_"


def _whole_word_pattern(word: str) -> re.Pattern:
    if word not in _WORD_PATTERN_CACHE:
        _WORD_PATTERN_CACHE[word] = re.compile(
            rf"(?<![{_BOUNDARY}]){re.escape(word)}(?![{_BOUNDARY}])"
        )
    return _WORD_PATTERN_CACHE[word]


def translate_output(stdout: str, reverse_map: dict | None = None) -> str:
    """Replace True/False/None as whole words, plus any embedded Python
    exception-message text (e.g. from a user's own `except ... as e:
    print(e)`) — that text originates from the interpreter, not from a
    string literal the user wrote, so it is translated like traceback
    text rather than preserved verbatim."""
    result = stdout
    for english, hindi in OUTPUT_MAP.items():
        result = _whole_word_pattern(english).sub(hindi, result)
    result = _translate_embedded_messages(result, reverse_map)
    return result


def translate_type(type_name: str) -> str:
    """"NameError" -> "नाम_त्रुटि" """
    return ERROR_TYPE_MAP.get(type_name, type_name)


_ITER_CALL_SUB = {
    "iterable": "दोहराने",
    "callable": "कॉल",
    "subscriptable": "सब्स्क्रिप्ट",
}


def _forward_map(reverse_map: dict | None) -> dict:
    """Invert a Hindi->English reverse_map into English->Hindi."""
    if not reverse_map:
        return {}
    return {english: hindi for hindi, english in reverse_map.items()}


def _to_hindi_name(name: str, forward_map: dict) -> str:
    """Restore an identifier embedded in an error message to its Hindi
    spelling when known. Names with no known mapping (e.g. a genuine typo
    the user never wrote) are shown verbatim."""
    return forward_map.get(name, name)


_MESSAGE_PATTERNS: list[tuple[re.Pattern, object]] = [
    (
        re.compile(r"^name '(.+)' is not defined$"),
        lambda m, fw: f"नाम '{_to_hindi_name(m.group(1), fw)}' परिभाषित नहीं है",
    ),
    (
        re.compile(r"^'(.+)' object has no attribute '(.+)'$"),
        lambda m, fw: (
            f"'{_to_hindi_name(m.group(1), fw)}' वस्तु में विशेषता "
            f"'{_to_hindi_name(m.group(2), fw)}' नहीं है"
        ),
    ),
    (
        re.compile(r"^(.+\(\)) takes (\d+) positional arguments? but (\d+) (?:was|were) given$"),
        lambda m, fw: f"{m.group(1)} को {m.group(2)} स्थितिगत तर्क चाहिए लेकिन {m.group(3)} दिए गए",
    ),
    (
        re.compile(r"^'(.+)' object is not (iterable|callable|subscriptable)$"),
        lambda m, fw: f"'{_to_hindi_name(m.group(1), fw)}' वस्तु {_ITER_CALL_SUB[m.group(2)]} योग्य नहीं है",
    ),
    (
        re.compile(r"^unsupported operand type\(s\) for (.+): '(.+)' and '(.+)'$"),
        lambda m, fw: f"'{m.group(2)}' और '{m.group(3)}' के लिए {m.group(1)} संक्रिया असमर्थित है",
    ),
    (
        re.compile(r'^can only concatenate str \(not "(.+)"\) to str$'),
        lambda m, fw: f'स्ट्रिंग को केवल स्ट्रिंग के साथ जोड़ा जा सकता है, "{m.group(1)}" के साथ नहीं',
    ),
    (
        re.compile(r"^invalid literal for int\(\) with base (\d+): '(.+)'$"),
        lambda m, fw: f"int() के लिए base {m.group(1)} में '{m.group(2)}' अवैध अक्षर है",
    ),
]

# Python 3.10+ appends this suggestion clause to NameError/AttributeError
# messages, e.g. "name 'dog1' is not defined. Did you mean: 'dog'?" — it
# sits outside the patterns above, so it's peeled off and translated
# separately, then the suggested name is restored to Hindi too.
_DID_YOU_MEAN_SUFFIX = re.compile(r"\.?\s*Did you mean:\s*'(.+)'\?\s*$")

# Unanchored twins of _MESSAGE_PATTERNS/_DID_YOU_MEAN_SUFFIX, for finding
# an exception message embedded anywhere within a larger string (e.g. a
# user's own print(e) call) rather than requiring the whole string to be
# exactly that message.
_MESSAGE_PATTERNS_SEARCH = [
    (re.compile(pattern.pattern.strip("^$")), builder) for pattern, builder in _MESSAGE_PATTERNS
]
_DID_YOU_MEAN_SEARCH = re.compile(r"\.?\s*Did you mean:\s*'(.+?)'\?")


def _translate_embedded_messages(text: str, reverse_map: dict | None) -> str:
    forward = _forward_map(reverse_map)

    text = _DID_YOU_MEAN_SEARCH.sub(
        lambda m: f"। क्या आपका मतलब '{_to_hindi_name(m.group(1), forward)}' से था?", text
    )

    for pattern, builder in _MESSAGE_PATTERNS_SEARCH:
        text = pattern.sub(lambda m, b=builder: b(m, forward), text)

    return text


def translate_message(msg: str, reverse_map: dict | None = None) -> str:
    """Run targeted regex patterns then fragment table."""
    forward = _forward_map(reverse_map)

    suggestion = ""
    suffix_match = _DID_YOU_MEAN_SUFFIX.search(msg)
    if suffix_match:
        suggested_name = _to_hindi_name(suffix_match.group(1), forward)
        suggestion = f"। क्या आपका मतलब '{suggested_name}' से था?"
        msg = msg[: suffix_match.start()]

    for pattern, builder in _MESSAGE_PATTERNS:
        match = pattern.match(msg)
        if match:
            return builder(match, forward) + suggestion

    result = msg
    for fragment, hindi in ERROR_MSG_MAP:
        result = result.replace(fragment, hindi)
    return result + suggestion


_FRAME_LINE_PATTERN = re.compile(r'^(\s*)File "(.+)", line (\d+), in (.+)$')
_TYPE_AND_MSG_PATTERN = re.compile(r"^([A-Za-z][A-Za-z0-9_.]*): (.+)$")
_TYPE_ONLY_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.]+$")


def translate_frame_line(line: str) -> str:
    """'  File "x", line 3, in foo' -> '  फ़ाइल "x", पंक्ति 3, में foo'"""
    match = _FRAME_LINE_PATTERN.match(line)
    if not match:
        return line
    indent, filename, lineno, func = match.groups()
    return f'{indent}फ़ाइल "{filename}", पंक्ति {lineno}, में {func}'


def translate_error(error_str: str, reverse_map: dict | None = None) -> str:
    """Walk traceback text line by line and translate each part."""
    if not error_str:
        return ""

    lines = error_str.splitlines()
    output_lines: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]

        if line.strip() == "Traceback (most recent call last):":
            output_lines.append(f"{TRACEBACK_WORD}:")
            i += 1
            continue

        if _FRAME_LINE_PATTERN.match(line):
            output_lines.append(translate_frame_line(line))
            i += 1
            if i < len(lines) and lines[i].startswith((" ", "\t")):
                output_lines.append(lines[i])  # source line, kept as-is
                i += 1
                if i < len(lines) and lines[i].lstrip().startswith("^"):
                    # Caret columns are computed against the compiled
                    # English source, not the Hindi line just shown —
                    # they'd point at the wrong characters, so drop
                    # rather than show a misaligned pointer.
                    i += 1
            continue

        type_msg_match = _TYPE_AND_MSG_PATTERN.match(line)
        if type_msg_match:
            error_type, message = type_msg_match.groups()
            output_lines.append(
                f"{translate_type(error_type)}: {translate_message(message, reverse_map)}"
            )
            i += 1
            continue

        if _TYPE_ONLY_PATTERN.match(line):
            output_lines.append(translate_type(line))
            i += 1
            continue

        output_lines.append(line)
        i += 1

    return "\n".join(output_lines)
