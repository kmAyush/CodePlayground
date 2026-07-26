"""Extract translatable identifiers from English Python source.

Returns a structured dict. Never translates anything.
"""

import ast
import textwrap

from core.constants import BUILTIN_METHODS, BUILTIN_NAMES, DUNDER

CATEGORIES = ("functions", "classes", "variables", "parameters", "attributes", "calls")


class _IdentifierVisitor(ast.NodeVisitor):
    def __init__(
        self,
        builtin_names: set[str] = BUILTIN_NAMES,
        builtin_methods: set[str] = BUILTIN_METHODS,
        self_name: str = "self",
    ):
        self.by_category = {category: [] for category in CATEGORIES}
        self.builtin_names = builtin_names
        self.builtin_methods = builtin_methods
        self.self_name = self_name

    def add(self, category: str, name: str | None) -> None:
        if not name or DUNDER(name) or name in self.builtin_names:
            return
        if category == "attributes" and name in self.builtin_methods:
            return
        bucket = self.by_category[category]
        if name not in bucket:
            bucket.append(name)

    def _visit_args(self, args: ast.arguments) -> None:
        all_args = [*args.posonlyargs, *args.args, *args.kwonlyargs]
        if args.vararg:
            all_args.append(args.vararg)
        if args.kwarg:
            all_args.append(args.kwarg)
        for arg in all_args:
            if arg.arg == self.self_name:
                continue
            self.add("parameters", arg.arg)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.add("functions", node.name)
        self._visit_args(node.args)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self._visit_args(node.args)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.add("classes", node.name)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id != self.self_name:
            self.add("variables", node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self.add("attributes", node.attr)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            self.add("calls", node.func.id)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self.add("variables", node.name)
        self.generic_visit(node)


def extract_identifiers(source: str) -> dict:
    source = textwrap.dedent(source).strip()
    tree = ast.parse(source)

    visitor = _IdentifierVisitor()
    visitor.visit(tree)

    flat_unique = sorted(
        {name for category in CATEGORIES for name in visitor.by_category[category]}
    )

    return {"by_category": visitor.by_category, "flat_unique": flat_unique}
