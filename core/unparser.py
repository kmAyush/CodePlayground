"""Walk a Python AST and emit Hindi Python source.

Never calls ast.unparse() for keywords. Never touches ast.Constant nodes
(besides emitting their repr unchanged).
"""

import ast

from core.constants import BUILTIN_METHODS, DUNDER, KEYWORD_MAP

SELF_HINDI = "स्वयं"

BIN_OPS: dict[type, str] = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.FloorDiv: "//",
    ast.Mod: "%",
    ast.Pow: "**",
    ast.LShift: "<<",
    ast.RShift: ">>",
    ast.BitAnd: "&",
    ast.BitOr: "|",
    ast.BitXor: "^",
    ast.MatMult: "@",
}

UNARY_OPS: dict[type, str] = {
    ast.UAdd: "+",
    ast.USub: "-",
    ast.Invert: "~",
}

COMPARE_OPS: dict[type, str] = {
    ast.Eq: "==",
    ast.NotEq: "!=",
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Gt: ">",
    ast.GtE: ">=",
}


class HindiUnparser:
    INDENT = "    "

    def __init__(self, name_map: dict[str, str]):
        self.name_map = name_map
        self.lines: list[str] = []
        self.depth = 0

    def visit(self, node: ast.AST) -> None:
        method = getattr(self, f"visit_{type(node).__name__}", None)
        if method is None:
            raise NotImplementedError(f"No visit_{type(node).__name__} handler")
        method(node)

    def render(self) -> str:
        return "\n".join(self.lines)

    def emit(self, text: str) -> None:
        self.lines.append(self.INDENT * self.depth + text)

    def _block(self, stmts: list[ast.stmt]) -> None:
        self.depth += 1
        for stmt in stmts:
            self.visit(stmt)
        self.depth -= 1

    # -- name resolution -------------------------------------------------

    def translate_name(self, name: str) -> str:
        if DUNDER(name):
            return name
        return self.name_map.get(name, name)

    def translate_attr(self, name: str) -> str:
        if DUNDER(name) or name in BUILTIN_METHODS:
            return name
        return self.name_map.get(name, name)

    def format_args(self, args: ast.arguments) -> str:
        parts: list[str] = []
        positional = [*args.posonlyargs, *args.args]
        defaults = list(args.defaults)
        num_no_default = len(positional) - len(defaults)

        for i, arg in enumerate(positional):
            name = SELF_HINDI if arg.arg == "self" else self.translate_name(arg.arg)
            if i >= num_no_default:
                name += f"={self.expr(defaults[i - num_no_default])}"
            parts.append(name)

        if args.vararg:
            parts.append("*" + self.translate_name(args.vararg.arg))
        elif args.kwonlyargs:
            parts.append("*")

        for arg, default in zip(args.kwonlyargs, args.kw_defaults):
            name = self.translate_name(arg.arg)
            if default is not None:
                name += f"={self.expr(default)}"
            parts.append(name)

        if args.kwarg:
            parts.append("**" + self.translate_name(args.kwarg.arg))

        return ", ".join(parts)

    def _emit_decorators(self, decorator_list: list[ast.expr]) -> None:
        for decorator in decorator_list:
            self.emit(f"@{self.expr(decorator)}")

    def _emit_blank_line_before_def(self) -> None:
        """Mirrors ast.unparse()'s leading self.maybe_newline() for
        FunctionDef/AsyncFunctionDef/ClassDef: one blank line before every
        def/class, skipped only when it's the very first thing emitted.

        This keeps line numbers 1:1 with the English source produced by
        ast.unparse() during execution (core/executor.py's
        hindi_to_english_source) — build_clean_traceback and the linecache
        registration in execute_hindi_source both index into hindi_source
        by that compiled source's line numbers, so any drift between the
        two renderings points tracebacks at the wrong line.
        """
        if self.lines:
            self.lines.append("")

    # -- expressions -------------------------------------------------------

    def expr(self, node: ast.AST) -> str:
        method = getattr(self, f"expr_{type(node).__name__}", None)
        if method is None:
            raise NotImplementedError(f"No expr_{type(node).__name__} handler")
        return method(node)

    def expr_Constant(self, node: ast.Constant) -> str:
        if node.value is Ellipsis:
            return "..."
        return repr(node.value)

    def expr_Name(self, node: ast.Name) -> str:
        if node.id == "self":
            return SELF_HINDI
        return self.translate_name(node.id)

    def expr_Attribute(self, node: ast.Attribute) -> str:
        return f"{self.expr(node.value)}.{self.translate_attr(node.attr)}"

    def expr_BinOp(self, node: ast.BinOp) -> str:
        op = BIN_OPS[type(node.op)]
        return f"{self.expr(node.left)} {op} {self.expr(node.right)}"

    def expr_UnaryOp(self, node: ast.UnaryOp) -> str:
        if isinstance(node.op, ast.Not):
            return f"{KEYWORD_MAP['not']} {self.expr(node.operand)}"
        op = UNARY_OPS[type(node.op)]
        return f"{op}{self.expr(node.operand)}"

    def expr_BoolOp(self, node: ast.BoolOp) -> str:
        word = KEYWORD_MAP["and"] if isinstance(node.op, ast.And) else KEYWORD_MAP["or"]
        return f" {word} ".join(self.expr(v) for v in node.values)

    def compare_op(self, op: ast.cmpop) -> str:
        if type(op) in COMPARE_OPS:
            return COMPARE_OPS[type(op)]
        if isinstance(op, ast.Is):
            return KEYWORD_MAP["is"]
        if isinstance(op, ast.IsNot):
            return f"{KEYWORD_MAP['is']} {KEYWORD_MAP['not']}"
        if isinstance(op, ast.In):
            return KEYWORD_MAP["in"]
        if isinstance(op, ast.NotIn):
            return f"{KEYWORD_MAP['not']} {KEYWORD_MAP['in']}"
        raise NotImplementedError(type(op))

    def expr_Compare(self, node: ast.Compare) -> str:
        result = self.expr(node.left)
        for op, comparator in zip(node.ops, node.comparators):
            result += f" {self.compare_op(op)} {self.expr(comparator)}"
        return result

    def expr_Call(self, node: ast.Call) -> str:
        func = self.expr(node.func)
        args = [self.expr(a) for a in node.args]
        for kw in node.keywords:
            if kw.arg is None:
                args.append(f"**{self.expr(kw.value)}")
            else:
                args.append(f"{self.translate_name(kw.arg)}={self.expr(kw.value)}")
        return f"{func}({', '.join(args)})"

    def expr_Tuple(self, node: ast.Tuple) -> str:
        items = [self.expr(e) for e in node.elts]
        if len(items) == 1:
            return f"({items[0]},)"
        return f"({', '.join(items)})"

    def expr_List(self, node: ast.List) -> str:
        return f"[{', '.join(self.expr(e) for e in node.elts)}]"

    def expr_Dict(self, node: ast.Dict) -> str:
        parts = []
        for key, value in zip(node.keys, node.values):
            if key is None:
                parts.append(f"**{self.expr(value)}")
            else:
                parts.append(f"{self.expr(key)}: {self.expr(value)}")
        return f"{{{', '.join(parts)}}}"

    def expr_Set(self, node: ast.Set) -> str:
        if not node.elts:
            return "set()"
        return f"{{{', '.join(self.expr(e) for e in node.elts)}}}"

    def format_comprehension(self, generators: list[ast.comprehension]) -> str:
        clauses = []
        for gen in generators:
            clause = (
                f"{KEYWORD_MAP['for']} {self.expr(gen.target)} "
                f"{KEYWORD_MAP['in']} {self.expr(gen.iter)}"
            )
            if gen.is_async:
                clause = f"{KEYWORD_MAP['async']} {clause}"
            for cond in gen.ifs:
                clause += f" {KEYWORD_MAP['if']} {self.expr(cond)}"
            clauses.append(clause)
        return " ".join(clauses)

    def expr_ListComp(self, node: ast.ListComp) -> str:
        return f"[{self.expr(node.elt)} {self.format_comprehension(node.generators)}]"

    def expr_SetComp(self, node: ast.SetComp) -> str:
        return f"{{{self.expr(node.elt)} {self.format_comprehension(node.generators)}}}"

    def expr_DictComp(self, node: ast.DictComp) -> str:
        return (
            f"{{{self.expr(node.key)}: {self.expr(node.value)} "
            f"{self.format_comprehension(node.generators)}}}"
        )

    def expr_GeneratorExp(self, node: ast.GeneratorExp) -> str:
        return f"({self.expr(node.elt)} {self.format_comprehension(node.generators)})"

    def expr_IfExp(self, node: ast.IfExp) -> str:
        return (
            f"{self.expr(node.body)} {KEYWORD_MAP['if']} {self.expr(node.test)} "
            f"{KEYWORD_MAP['else']} {self.expr(node.orelse)}"
        )

    def expr_Lambda(self, node: ast.Lambda) -> str:
        args = self.format_args(node.args)
        body = self.expr(node.body)
        if args:
            return f"{KEYWORD_MAP['lambda']} {args}: {body}"
        return f"{KEYWORD_MAP['lambda']}: {body}"

    def expr_Subscript(self, node: ast.Subscript) -> str:
        return f"{self.expr(node.value)}[{self.expr(node.slice)}]"

    def expr_Slice(self, node: ast.Slice) -> str:
        lower = self.expr(node.lower) if node.lower is not None else ""
        upper = self.expr(node.upper) if node.upper is not None else ""
        if node.step is not None:
            return f"{lower}:{upper}:{self.expr(node.step)}"
        return f"{lower}:{upper}"

    def expr_JoinedStr(self, node: ast.JoinedStr) -> str:
        parts = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            elif isinstance(value, ast.FormattedValue):
                inner = self.expr(value.value)
                conv = f"!{chr(value.conversion)}" if value.conversion != -1 else ""
                spec = ""
                if value.format_spec is not None:
                    spec = ":" + "".join(
                        v.value if isinstance(v, ast.Constant) else self.expr(v)
                        for v in value.format_spec.values
                    )
                parts.append(f"{{{inner}{conv}{spec}}}")
        return 'f"' + "".join(parts) + '"'

    def expr_Starred(self, node: ast.Starred) -> str:
        return f"*{self.expr(node.value)}"

    def expr_Await(self, node: ast.Await) -> str:
        return f"{KEYWORD_MAP['await']} {self.expr(node.value)}"

    def expr_Yield(self, node: ast.Yield) -> str:
        if node.value is None:
            return KEYWORD_MAP["yield"]
        return f"{KEYWORD_MAP['yield']} {self.expr(node.value)}"

    def expr_YieldFrom(self, node: ast.YieldFrom) -> str:
        return f"{KEYWORD_MAP['yield']} {KEYWORD_MAP['from']} {self.expr(node.value)}"

    # -- statements ----------------------------------------------------

    def visit_Module(self, node: ast.Module) -> None:
        for stmt in node.body:
            self.visit(stmt)

    def visit_Expr(self, node: ast.Expr) -> None:
        self.emit(self.expr(node.value))

    def visit_Assign(self, node: ast.Assign) -> None:
        targets = " = ".join(self.expr(t) for t in node.targets)
        self.emit(f"{targets} = {self.expr(node.value)}")

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        op = BIN_OPS[type(node.op)]
        self.emit(f"{self.expr(node.target)} {op}= {self.expr(node.value)}")

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        target = self.expr(node.target)
        annotation = self.expr(node.annotation)
        if node.value is not None:
            self.emit(f"{target}: {annotation} = {self.expr(node.value)}")
        else:
            self.emit(f"{target}: {annotation}")

    def visit_Return(self, node: ast.Return) -> None:
        if node.value is None:
            self.emit(KEYWORD_MAP["return"])
        else:
            self.emit(f"{KEYWORD_MAP['return']} {self.expr(node.value)}")

    def visit_Delete(self, node: ast.Delete) -> None:
        targets = ", ".join(self.expr(t) for t in node.targets)
        self.emit(f"{KEYWORD_MAP['del']} {targets}")

    def visit_Pass(self, node: ast.Pass) -> None:
        self.emit(KEYWORD_MAP["pass"])

    def visit_Break(self, node: ast.Break) -> None:
        self.emit(KEYWORD_MAP["break"])

    def visit_Continue(self, node: ast.Continue) -> None:
        self.emit(KEYWORD_MAP["continue"])

    def visit_Assert(self, node: ast.Assert) -> None:
        if node.msg is not None:
            self.emit(f"{KEYWORD_MAP['assert']} {self.expr(node.test)}, {self.expr(node.msg)}")
        else:
            self.emit(f"{KEYWORD_MAP['assert']} {self.expr(node.test)}")

    def visit_Global(self, node: ast.Global) -> None:
        names = ", ".join(self.translate_name(n) for n in node.names)
        self.emit(f"{KEYWORD_MAP['global']} {names}")

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        names = ", ".join(self.translate_name(n) for n in node.names)
        self.emit(f"{KEYWORD_MAP['nonlocal']} {names}")

    def visit_Raise(self, node: ast.Raise) -> None:
        if node.exc is None:
            self.emit(KEYWORD_MAP["raise"])
            return
        text = f"{KEYWORD_MAP['raise']} {self.expr(node.exc)}"
        if node.cause is not None:
            text += f" {KEYWORD_MAP['from']} {self.expr(node.cause)}"
        self.emit(text)

    def _format_alias(self, alias: ast.alias) -> str:
        display_name = self.translate_name(alias.name)
        if alias.asname:
            display_asname = self.translate_name(alias.asname)
            return f"{display_name} {KEYWORD_MAP['as']} {display_asname}"
        return display_name

    def visit_Import(self, node: ast.Import) -> None:
        names = ", ".join(self._format_alias(a) for a in node.names)
        self.emit(f"{KEYWORD_MAP['import']} {names}")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        dots = "." * node.level
        names = ", ".join(self._format_alias(a) for a in node.names)
        self.emit(f"{KEYWORD_MAP['from']} {dots}{module} {KEYWORD_MAP['import']} {names}")

    def visit_If(self, node: ast.If) -> None:
        self.emit(f"{KEYWORD_MAP['if']} {self.expr(node.test)}:")
        self._block(node.body)

        orelse = node.orelse
        while len(orelse) == 1 and isinstance(orelse[0], ast.If):
            elif_node = orelse[0]
            self.emit(f"{KEYWORD_MAP['elif']} {self.expr(elif_node.test)}:")
            self._block(elif_node.body)
            orelse = elif_node.orelse

        if orelse:
            self.emit(f"{KEYWORD_MAP['else']}:")
            self._block(orelse)

    def visit_For(self, node: ast.For) -> None:
        self.emit(
            f"{KEYWORD_MAP['for']} {self.expr(node.target)} "
            f"{KEYWORD_MAP['in']} {self.expr(node.iter)}:"
        )
        self._block(node.body)
        if node.orelse:
            self.emit(f"{KEYWORD_MAP['else']}:")
            self._block(node.orelse)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.emit(
            f"{KEYWORD_MAP['async']} {KEYWORD_MAP['for']} {self.expr(node.target)} "
            f"{KEYWORD_MAP['in']} {self.expr(node.iter)}:"
        )
        self._block(node.body)
        if node.orelse:
            self.emit(f"{KEYWORD_MAP['else']}:")
            self._block(node.orelse)

    def visit_While(self, node: ast.While) -> None:
        self.emit(f"{KEYWORD_MAP['while']} {self.expr(node.test)}:")
        self._block(node.body)
        if node.orelse:
            self.emit(f"{KEYWORD_MAP['else']}:")
            self._block(node.orelse)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._emit_blank_line_before_def()
        self._emit_decorators(node.decorator_list)
        name = self.translate_name(node.name)
        args = self.format_args(node.args)
        self.emit(f"{KEYWORD_MAP['def']} {name}({args}):")
        self._block(node.body)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._emit_blank_line_before_def()
        self._emit_decorators(node.decorator_list)
        name = self.translate_name(node.name)
        args = self.format_args(node.args)
        self.emit(f"{KEYWORD_MAP['async']} {KEYWORD_MAP['def']} {name}({args}):")
        self._block(node.body)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._emit_blank_line_before_def()
        self._emit_decorators(node.decorator_list)
        name = self.translate_name(node.name)
        bases = [self.expr(b) for b in node.bases]
        for kw in node.keywords:
            bases.append(f"{kw.arg}={self.expr(kw.value)}")
        if bases:
            self.emit(f"{KEYWORD_MAP['class']} {name}({', '.join(bases)}):")
        else:
            self.emit(f"{KEYWORD_MAP['class']} {name}:")
        self._block(node.body)

    def visit_Try(self, node: ast.Try) -> None:
        self.emit(f"{KEYWORD_MAP['try']}:")
        self._block(node.body)

        for handler in node.handlers:
            if handler.type is not None:
                type_str = self.expr(handler.type)
                if handler.name:
                    self.emit(f"{KEYWORD_MAP['except']} {type_str} {KEYWORD_MAP['as']} {handler.name}:")
                else:
                    self.emit(f"{KEYWORD_MAP['except']} {type_str}:")
            else:
                self.emit(f"{KEYWORD_MAP['except']}:")
            self._block(handler.body)

        if node.orelse:
            self.emit(f"{KEYWORD_MAP['else']}:")
            self._block(node.orelse)

        if node.finalbody:
            self.emit(f"{KEYWORD_MAP['finally']}:")
            self._block(node.finalbody)

    def _format_with_items(self, items: list[ast.withitem]) -> str:
        parts = []
        for item in items:
            text = self.expr(item.context_expr)
            if item.optional_vars is not None:
                text += f" {KEYWORD_MAP['as']} {self.expr(item.optional_vars)}"
            parts.append(text)
        return ", ".join(parts)

    def visit_With(self, node: ast.With) -> None:
        self.emit(f"{KEYWORD_MAP['with']} {self._format_with_items(node.items)}:")
        self._block(node.body)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self.emit(
            f"{KEYWORD_MAP['async']} {KEYWORD_MAP['with']} {self._format_with_items(node.items)}:"
        )
        self._block(node.body)
