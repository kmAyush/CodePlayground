"""Execute Hindi Python source. Return Hindi output and Hindi errors.

Never shows internal executor frames to the user.
"""

import ast
import io
import linecache
import re
import sys
import traceback as tb

from core.constants import DUNDER, KEYWORD_MAP, TRACEBACK_WORD
from core.output_translator import (
    translate_error,
    translate_message,
    translate_output,
    translate_type,
)
from core.unparser import SELF_HINDI

REVERSE_KEYWORD_MAP: dict[str, str] = {v: k for k, v in KEYWORD_MAP.items()}
_SORTED_HINDI_KEYWORDS = sorted(REVERSE_KEYWORD_MAP.keys(), key=len, reverse=True)
_BOUNDARY = "a-zA-Zऀ-ॿ_"
_KEYWORD_PATTERN = re.compile(
    rf"(?<![{_BOUNDARY}])(?:{'|'.join(re.escape(k) for k in _SORTED_HINDI_KEYWORDS)})(?![{_BOUNDARY}])"
)


def restore_keywords(source: str) -> str:
    return _KEYWORD_PATTERN.sub(lambda m: REVERSE_KEYWORD_MAP[m.group(0)], source)


class EnglishRestorer(ast.NodeTransformer):
    def __init__(self, reverse_map: dict[str, str]):
        self.reverse_map = reverse_map

    def restore(self, name: str) -> str:
        if name == SELF_HINDI:
            return "self"
        if DUNDER(name):
            return name
        return self.reverse_map.get(name, name)

    def visit_Name(self, node: ast.Name) -> ast.AST:
        self.generic_visit(node)
        node.id = self.restore(node.id)
        return node

    def visit_arg(self, node: ast.arg) -> ast.AST:
        self.generic_visit(node)
        node.arg = self.restore(node.arg)
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        self.generic_visit(node)
        node.attr = self.restore(node.attr)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self.generic_visit(node)
        node.name = self.restore(node.name)
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        self.generic_visit(node)
        node.name = self.restore(node.name)
        return node

    def visit_Global(self, node: ast.Global) -> ast.AST:
        self.generic_visit(node)
        node.names = [self.restore(n) for n in node.names]
        return node

    def visit_Nonlocal(self, node: ast.Nonlocal) -> ast.AST:
        self.generic_visit(node)
        node.names = [self.restore(n) for n in node.names]
        return node

    def _restore_alias(self, alias: ast.alias) -> None:
        alias.name = self.restore(alias.name)
        if alias.asname:
            alias.asname = self.restore(alias.asname)

    def visit_Import(self, node: ast.Import) -> ast.AST:
        for alias in node.names:
            self._restore_alias(alias)
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST:
        if node.module:
            node.module = self.restore(node.module)
        for alias in node.names:
            self._restore_alias(alias)
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        return node


def _find_hindi_name(english_name: str, reverse_map: dict[str, str]) -> str:
    for hindi, english in reverse_map.items():
        if english == english_name:
            return hindi
    return english_name


def build_clean_traceback(
    exc: BaseException, hindi_source: str, reverse_map: dict[str, str]
) -> str:
    frames = tb.extract_tb(exc.__traceback__)
    user_frames = [frame for frame in frames if frame.filename == "<hindi>"]
    hindi_lines = hindi_source.splitlines()

    lines = [f"{TRACEBACK_WORD}:"]
    for frame in user_frames:
        hindi_func = _find_hindi_name(frame.name, reverse_map)
        lines.append(f'  फ़ाइल "<hindi>", पंक्ति {frame.lineno}, में {hindi_func}')
        if frame.lineno and 0 < frame.lineno <= len(hindi_lines):
            lines.append(f"    {hindi_lines[frame.lineno - 1].strip()}")

    error_type = type(exc).__name__
    message = str(exc)
    if message:
        lines.append(f"{translate_type(error_type)}: {translate_message(message, reverse_map)}")
    else:
        lines.append(translate_type(error_type))

    return "\n".join(lines)


def hindi_to_english_source(hindi_source: str, reverse_map: dict[str, str]) -> str:
    """Restore Hindi source to clean, executable English Python (no exec)."""
    keyword_restored = restore_keywords(hindi_source)
    tree = ast.parse(keyword_restored)
    EnglishRestorer(reverse_map).visit(tree)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def execute_hindi_source(
    hindi_source: str,
    reverse_map: dict[str, str],
    exec_globals: dict | None = None,
) -> tuple[str, str]:
    try:
        english_source = hindi_to_english_source(hindi_source, reverse_map)
    except SyntaxError as exc:
        return "", build_clean_traceback(exc, hindi_source, reverse_map)

    if exec_globals is None:
        exec_globals = {}
    exec_globals.setdefault("__name__", "__main__")

    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = stdout_capture
    sys.stderr = stderr_capture
    # Let Python's own traceback formatting (e.g. a user's own
    # `except ... as e: traceback.print_exc()`) find the Hindi source line
    # for "<hindi>" frames — mirrors what build_clean_traceback already
    # does manually for the uncaught-exception path below.
    linecache.cache["<hindi>"] = (
        len(hindi_source),
        None,
        hindi_source.splitlines(keepends=True),
        "<hindi>",
    )
    try:
        compiled = compile(english_source, "<hindi>", "exec")
        exec(compiled, exec_globals)
    except Exception as exc:
        prior_stderr = translate_error(stderr_capture.getvalue(), reverse_map)
        traceback_text = build_clean_traceback(exc, hindi_source, reverse_map)
        combined_error = f"{prior_stderr}\n{traceback_text}" if prior_stderr else traceback_text
        return "", combined_error
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        linecache.cache.pop("<hindi>", None)

    raw_stdout = stdout_capture.getvalue()
    raw_stderr = stderr_capture.getvalue()
    return translate_output(raw_stdout, reverse_map), translate_error(raw_stderr, reverse_map)
