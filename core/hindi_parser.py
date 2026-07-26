"""Extract identifiers from Hindi Python source (after keyword restoration).

Mirror of parser.py but skips REVERSE_BUILTIN_MAP names instead of
BUILTIN_NAMES. Called when a user writes Hindi from scratch (no
project.json / reverse_map exists yet).
"""

import ast

from core.constants import REVERSE_BUILTIN_MAP
from core.executor import restore_keywords
from core.parser import CATEGORIES, _IdentifierVisitor
from core.unparser import SELF_HINDI


def extract_hindi_identifiers(hindi_source: str) -> dict:
    restored = restore_keywords(hindi_source)
    tree = ast.parse(restored)

    visitor = _IdentifierVisitor(
        builtin_names=set(REVERSE_BUILTIN_MAP.keys()),
        builtin_methods=set(),
        self_name=SELF_HINDI,
    )
    visitor.visit(tree)

    flat_unique = sorted(
        {name for category in CATEGORIES for name in visitor.by_category[category]}
    )

    return {"by_category": visitor.by_category, "flat_unique": flat_unique}
