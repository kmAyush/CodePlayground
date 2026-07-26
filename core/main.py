"""CLI orchestrator for the core translation/execution pipeline.

Not the web app entry point — see backend/app.py for that (Phase 2).
"""

import ast
import json
import sys
import textwrap
from pathlib import Path

from core.constants import BUILTIN_MAP, REVERSE_BUILTIN_MAP
from core.executor import execute_hindi_source
from core.hindi_parser import extract_hindi_identifiers
from core.llm_call import translate_identifiers
from core.llm_reverse import reverse_translate_identifiers
from core.parser import extract_identifiers
from core.unparser import HindiUnparser

PROJECT_FILE_NAME = "project.json"


def translate_source(source: str, verbose: bool = True) -> tuple[str, dict]:
    """English source -> (hindi_source, reverse_map).

    reverse_map includes both LLM translations and REVERSE_BUILTIN_MAP.
    """
    identifiers = extract_identifiers(source)
    flat_unique = identifiers["flat_unique"]

    if verbose:
        print(f"Translating {len(flat_unique)} identifier(s)...", file=sys.stderr)

    translation_map = translate_identifiers(flat_unique)
    name_map = {**translation_map, **BUILTIN_MAP}

    tree = ast.parse(textwrap.dedent(source).strip())
    unparser = HindiUnparser(name_map)
    unparser.visit(tree)
    hindi_source = unparser.render()

    reverse_from_translation = {v: k for k, v in translation_map.items()}
    reverse_map = {**reverse_from_translation, **REVERSE_BUILTIN_MAP}

    return hindi_source, reverse_map


def run_hindi_source(hindi_source: str, reverse_map: dict) -> tuple[str, str]:
    """Hindi source + reverse_map -> (hindi_stdout, hindi_error)."""
    return execute_hindi_source(hindi_source, reverse_map)


def _load_reverse_map(project_file: Path) -> dict:
    data = json.loads(project_file.read_text(encoding="utf-8"))
    return {**data.get("reverse_map", {}), **REVERSE_BUILTIN_MAP}


def run_hindi_file(filepath: str) -> tuple[str, str]:
    """Entry point for running a .py file written in Hindi.

    Loads project.json if it exists alongside the file (reverse_map).
    Falls back to hindi_parser + llm_reverse if not.
    """
    path = Path(filepath)
    hindi_source = path.read_text(encoding="utf-8")

    project_file = path.parent / PROJECT_FILE_NAME
    if project_file.exists():
        reverse_map = _load_reverse_map(project_file)
    else:
        identifiers = extract_hindi_identifiers(hindi_source)
        translation_map = reverse_translate_identifiers(identifiers["flat_unique"])
        reverse_map = {**translation_map, **REVERSE_BUILTIN_MAP}

    return run_hindi_source(hindi_source, reverse_map)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m core.main <hindi_file.py>", file=sys.stderr)
        sys.exit(1)

    stdout, error = run_hindi_file(sys.argv[1])
    if stdout:
        print(stdout, end="")
    if error:
        print(error, file=sys.stderr)
        sys.exit(1)
