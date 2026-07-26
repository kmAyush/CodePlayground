# CLAUDE.md — Hindi Python Playground

## Project Overview

A bilingual Python IDE web-app with two panels — left panel (Hindi) and right panel
(English). Writing in either panel live-syncs the other via debounced translation.
A Run button executes the code and shows output/errors in both languages simultaneously.

## Key Decisions (locked — do not revisit)

- **Sync strategy**: Option A — Live sync, debounced 800ms
- **Execution isolation**: Option A — subprocess with 5s timeout
- **Translation core**: AST-based (not regex/LLM-only)
- **LLM provider**: Sarvam AI (`sarvam-30b`)
- **Backend**: FastAPI + uvicorn
- **Frontend**: Vanilla JS + CodeMirror 6

---

## SOLID Principles Applied

| Principle | How It Applies |
|---|---|
| **S** — Single Responsibility | Each file owns exactly one concern. `parser.py` only extracts. `executor.py` only runs. `unparser.py` only emits. |
| **O** — Open/Closed | `HindiUnparser` is extended by adding `visit_*`/`expr_*` methods. `KEYWORD_MAP` and `BUILTIN_MAP` in `constants.py` are extended by adding entries, never by modifying callers. |
| **L** — Liskov | `EnglishRestorer` extends `ast.NodeTransformer` and can substitute it anywhere a transformer is expected. |
| **I** — Interface Segregation | Routes are split — `/translate` routes import only translation modules. `/execute` routes import only executor. Neither imports the other. |
| **D** — Dependency Inversion | `executor.py` depends on `reverse_map: dict` (abstraction), not on any specific LLM or session implementation. `main.py` wires the concrete implementations. |

---

## Repository Structure

```
hindi-playground/
│
├── CLAUDE.md                        ← this file
├── .env                             ← SARVAM_API key (never commit)
├── .env.example                     ← template for .env
├── pyproject.toml                   ← uv project config
├── README.md
│
├── core/                            ← Phase 1: pure Python, no web
│   ├── __init__.py
│   ├── constants.py                 ← all lookup tables, zero logic
│   ├── parser.py                    ← English AST identifier extraction
│   ├── hindi_parser.py              ← Hindi AST identifier extraction
│   ├── llm_call.py                  ← English→Hindi LLM translation
│   ├── llm_reverse.py               ← Hindi→English LLM translation
│   ├── unparser.py                  ← AST → Hindi source string
│   ├── executor.py                  ← Hindi source → exec → output
│   └── output_translator.py         ← stdout/stderr → Hindi text
│
├── backend/                         ← Phase 2: FastAPI
│   ├── __init__.py
│   ├── app.py                       ← FastAPI app factory
│   ├── session.py                   ← in-memory session store
│   ├── sandbox.py                   ← subprocess isolation wrapper
│   └── routes/
│       ├── __init__.py
│       ├── translate.py             ← /translate/* endpoints
│       └── execute.py               ← /execute/* endpoints
│
├── frontend/                        ← Phase 3: browser UI
│   ├── index.html
│   ├── style.css
│   ├── hindi-mode.js                ← CodeMirror Hindi keyword highlighter
│   ├── editor.js                    ← panel setup, debounce, sync logic
│   └── api.js                       ← fetch wrappers for all endpoints
│
└── test/                            ← all tests, all phases
    ├── core/
    │   ├── test_constants.py
    │   ├── test_parser.py
    │   ├── test_hindi_parser.py
    │   ├── test_llm_call.py
    │   ├── test_llm_reverse.py
    │   ├── test_unparser.py
    │   ├── test_executor_success.py
    │   ├── test_executor_errors.py
    │   └── test_output_translator.py
    ├── backend/
    │   ├── test_session.py
    │   ├── test_sandbox.py
    │   ├── test_routes_translate.py
    │   └── test_routes_execute.py
    └── frontend/
        └── test_debounce.js         ← manual browser test checklist
```

---

## Phase 1 — Core Translation Engine

**Goal**: A fully working English↔Hindi translation and execution pipeline
with no web layer. All logic is pure Python. Every module is independently
testable.

**Complete when**: All `test/core/` tests pass. The pipeline can be run
end-to-end from the command line.

---

### Phase 1.1 — `core/constants.py`

**Single responsibility**: Static lookup tables. Zero logic. Zero imports
from within the project.

**Contains**:

```
KEYWORD_MAP          dict[str, str]   Python keyword → Hindi keyword
                                      "def"→"काम", "if"→"अगर" ...

BUILTIN_MAP          dict[str, str]   Python builtin → Hindi builtin
                                      "print"→"छापो", "len"→"लंबाई" ...

BUILTIN_NAMES        set[str]         keys of BUILTIN_MAP
                                      used by parser.py to skip extraction

BUILTIN_METHODS      set[str]         empty by default — populate to keep
                                      specific methods in English display

REVERSE_BUILTIN_MAP  dict[str, str]   {v:k for k,v in BUILTIN_MAP.items()}
                                      Hindi builtin → English builtin

OUTPUT_MAP           dict[str, str]   "True"→"सच", "False"→"झूठ", "None"→"कुछनहीं"

ERROR_TYPE_MAP       dict[str, str]   "NameError"→"नाम_त्रुटि" ... (35 entries)

ERROR_MSG_MAP        list[tuple]      ordered longest-first fragment pairs
                                      [("is not defined", "परिभाषित नहीं है"), ...]

TRACEBACK_WORD       str              "पिछलावा"

DUNDER               lambda           name → bool  (__init__, __name__, ...)
```

**Test file**: `test/core/test_constants.py`

```
- BUILTIN_NAMES == set(BUILTIN_MAP.keys())
- REVERSE_BUILTIN_MAP is the exact inverse of BUILTIN_MAP
- No key appears in both KEYWORD_MAP and BUILTIN_MAP
- ERROR_MSG_MAP is sorted longest-first (len(a[0]) >= len(b[0]))
- DUNDER("__init__") is True
- DUNDER("greet") is False
```

---

### Phase 1.2 — `core/parser.py`

**Single responsibility**: Extract translatable identifiers from English
Python source. Returns structured dict. Never translates anything.

**Public API**:

```python
def extract_identifiers(source: str) -> dict:
    """
    Returns:
        {
          "by_category": {
            "functions":  ["greet", "main"],
            "classes":    ["Animal"],
            "variables":  ["name", "message"],
            "parameters": ["name", "sound"],
            "attributes": ["name", "sound"],    ← Attribute.attr nodes
            "calls":      ["greet"]
          },
          "flat_unique": ["greet", "main", "message", "name", "sound"]
        }

    Rules:
        - textwrap.dedent().strip() source before ast.parse()
        - Skip DUNDER names
        - Skip names in BUILTIN_NAMES
        - Skip names in BUILTIN_METHODS (for attributes)
        - Deduplicate across categories in flat_unique
        - flat_unique is sorted alphabetically
    """
```

**Test file**: `test/core/test_parser.py`

```
- Basic function: extracts function name and parameter names
- Class: extracts class name, method names, self excluded
- Dict + for: extracts variable names, not string keys
- __name__ guard: __name__ and __main__ not in flat_unique
- Builtins: print, len, range not in flat_unique
- Attributes: self.name → "name" in attributes category
- Deduplication: same name in multiple categories appears once in flat_unique
- Empty source: returns empty by_category and flat_unique
- textwrap.dedent: indented triple-quoted string parses without IndentationError
```

---

### Phase 1.3 — `core/llm_call.py`

**Single responsibility**: Send English identifiers to Sarvam LLM.
Return Hindi translation map. Handle all API errors.

**Public API**:

```python
def translate_identifiers(flat_unique: list[str]) -> dict[str, str]:
    """
    Parameters:
        flat_unique: ["greet", "message", "name"]

    Returns:
        {"greet": "स्वागत", "message": "संदेश", "name": "नाम"}

    Rules:
        - Empty list → return {} immediately (no API call)
        - temperature=0.1, reasoning_effort=None, max_tokens=1024
        - finish_reason="length" → raise RuntimeError with batch size hint
        - Empty content → raise RuntimeError
        - Invalid JSON → raise RuntimeError with raw response preview
        - Missing identifiers → fill with original English (no KeyError downstream)
        - ApiError 401/403/422/429/500 → raise RuntimeError with status code
    """
```

**System prompt behaviour**:

```
- Input:  JSON {"identifiers": ["student", "marks", "items", "append"]}
- Output: JSON {"student":"छात्र","marks":"अंक","items":"मदें","append":"जोड़ो"}
- Translate ALL identifiers including method names like items, append, split
- snake_case for multi-word: "student_marks" → "छात्र_अंक"
- Pure Devanagari output — no English in values
- No markdown fences, no explanation, JSON only
```

**Test file**: `test/core/test_llm_call.py`

```
- Empty list: returns {} without API call
- Valid identifiers: returns dict with all keys present
- Missing key fallback: if LLM omits an identifier, original fills it
- finish_reason=length: RuntimeError raised (mock the response)
- Empty content: RuntimeError raised (mock the response)
- Invalid JSON: RuntimeError raised with raw preview (mock)
- API 429: RuntimeError with "Rate limit" message (mock)
```

---

### Phase 1.4 — `core/unparser.py`

**Single responsibility**: Walk a Python AST and emit Hindi Python source.
Never calls `ast.unparse()` for keywords. Never touches `ast.Constant` nodes.

**Public API**:

```python
class HindiUnparser:
    def __init__(self, name_map: dict[str, str]):
        """
        name_map: merged {**translation_map, **BUILTIN_MAP}
        Builtins always win (right-side merge in caller).
        """

    def visit(self, node: ast.AST) -> None:
        """Entry point. Call with ast.Module node."""

    def render(self) -> str:
        """Return complete Hindi Python source string."""
```

**Internal structure**:

```
visit_* methods    → handle statements, call self.emit()
expr_* methods     → handle expressions, return str
emit(text)         → append INDENT*depth + text to self.lines
_block(stmts)      → depth+1, visit each stmt, depth-1
render()           → "\n".join(self.lines)

Nodes with visit_* handlers (minimum):
  Module, Expr, Assign, AugAssign, AnnAssign,
  Return, Delete, Pass, Break, Continue, Assert,
  Global, Nonlocal, Raise, Import, ImportFrom,
  If, For, While, FunctionDef, AsyncFunctionDef,
  ClassDef, Try, With, AsyncFor, AsyncWith

Nodes with expr_* handlers (minimum):
  Constant, Name, BinOp, UnaryOp, BoolOp, Compare,
  Call, Attribute, Tuple, List, Dict, Set,
  ListComp, SetComp, DictComp, GeneratorExp,
  IfExp, Lambda, Subscript, Slice, JoinedStr,
  Starred, Await, Yield, YieldFrom
```

**Critical rules**:

```
- Constant nodes: return repr(node.value), never translate
- Attribute.attr: look up in name_map (user-defined) — translate
- Dunder names: pass through unchanged (__init__, __name__)
- elif chains: detect orelse=[ast.If] pattern, emit "नहींतो" not nested "अगर"
- self → स्वयं: handled in format_args()
- KEYWORD_MAP is defined at module level in unparser.py (not in constants.py)
  because it is structural — it defines the output grammar
```

**Test file**: `test/core/test_unparser.py`

```
- Hello world: छापो("Hello") emitted correctly
- if/elif/else: नहींतो emitted for elif (not nested अगर/वरना)
- for loop: केलिए...में emitted
- function def: काम emitted, self→स्वयं
- class: क्लास emitted
- try/except/finally: कोशिश/सिवाय/अंत_में emitted
- Constant strings: never translated ("Hello" stays "Hello")
- Dunder preserved: __init__ stays __init__
- __name__ guard: अगर __name__ == '__main__': emitted correctly
- list comprehension: [x केलिए x में श्रेणी(5)] correct
- lambda: लैम्ब्डा x: x*2 correct
- Indentation: 4 spaces per level, verified with splitlines()
```

---

### Phase 1.5 — `core/executor.py`

**Single responsibility**: Execute Hindi Python source. Return Hindi output
and Hindi errors. Never show internal frames to the user.

**Public API**:

```python
def execute_hindi_source(
    hindi_source: str,
    reverse_map: dict[str, str],
    exec_globals: dict = None,
) -> tuple[str, str]:
    """
    Returns: (hindi_stdout, hindi_error)
    hindi_error is "" on success.

    Internal stages:
        1. restore_keywords(source)      text sub, Hindi kw → English kw
        2. ast.parse(keyword_restored)   now valid Python syntax
        3. EnglishRestorer.visit(tree)   Hindi identifiers → English
        4. ast.unparse(new_tree)         clean English Python
        5. exec(compile(..., "<hindi>")) stdout captured
        6. build_clean_traceback()       user frames only, Hindi output
        7. translate_output(stdout)      True/False/None → Hindi
    """
```

**`restore_keywords` rules**:

```
- Build REVERSE_KEYWORD_MAP = {v:k for k,v in KEYWORD_MAP.items()} at import time
- Sort by descending key length before substitution
- Use Unicode-aware word boundary regex:
    (?<![a-zA-Z\u0900-\u097F_]) + keyword + (?![a-zA-Z\u0900-\u097F_])
- Prevents "में" matching inside "समूह"
```

**`EnglishRestorer` rules**:

```
- Extends ast.NodeTransformer
- restore(name): DUNDER → keep, else reverse_map.get(name, name)
- visit_arg: "स्वयं" → "self" always
- visit_Attribute: generic_visit first (restore object), then restore attr
- visit_Constant: return node unchanged
- visit_Global / visit_Nonlocal: restore each name in node.names list
```

**`build_clean_traceback` rules**:

```
- tb.extract_tb(exc_tb) → filter filename == "<hindi>" only
- For each user frame:
    - Walk reverse_map to find Hindi function name for display
    - Pull Hindi source line by lineno from original hindi_source
- Call translate_type() and translate_message() from output_translator
- Format: पिछलावा header, फ़ाइल/पंक्ति/में frame lines, error type: message
- Never expose executor.py internal frames
```

**Test file**: `test/core/test_executor_success.py`

```
- Hello world: stdout="नमस्ते दुनिया\n", error=""
- Arithmetic: print(2+3) → "5\n"
- Function def and call: returns correct value
- Class instantiation and method call
- for loop output: "0\n1\n2\n"
- while loop with break
- try/except catches error: no error in output
- __name__ guard: main() executes correctly
- True/False/None in output → सच/झूठ/कुछनहीं
- stdout restored after error (sys.stdout is original after call)
```

**Test file**: `test/core/test_executor_errors.py`

```
- NameError: पिछलावा present, नाम_त्रुटि present, परिभाषित नहीं है present
- TypeError wrong args: प्रकार_त्रुटि present, स्थितिगत तर्क present
- TypeError str+int: स्ट्रिंग present
- ZeroDivisionError: शून्य_भाग_त्रुटि present, शून्य से भाग present
- IndexError: अनुक्रमणिका_त्रुटि present
- KeyError: कुंजी_त्रुटि present
- AttributeError: विशेषता_त्रुटि present
- RecursionError: पुनरावर्तन_त्रुटि present
- Multi-frame: all user frames present, executor.py frame absent
- "Traceback" English word: must NOT appear in any error output
- "most recent call last" English: must NOT appear in any error output
```

---

### Phase 1.6 — `core/output_translator.py`

**Single responsibility**: Translate Python's English output tokens and
traceback text to Hindi. Never modifies user string values.

**Public API**:

```python
def translate_output(stdout: str, reverse_map: dict) -> str:
    """Replace True/False/None as whole words only."""

def translate_error(error_str: str, reverse_map: dict) -> str:
    """Walk traceback text line by line and translate each part."""

def translate_type(type_name: str) -> str:
    """"NameError" → "नाम_त्रुटि" """

def translate_message(msg: str) -> str:
    """Run targeted regex patterns then fragment table."""

def translate_frame_line(line: str) -> str:
    """'  File "x", line 3, in foo' → '  फ़ाइल "x", पंक्ति 3, में foo'"""
```

**`translate_error` line-type dispatch**:

```
"Traceback (most recent call last):"   → emit पिछलावा header
/^\s*File ".+", line \d+, in .+$/     → translate_frame_line()
    next line (source code)            → keep as-is (already Hindi)
    next line starting with ^          → keep as-is (caret pointer)
/^[A-Za-z][A-Za-z0-9_.]*: .+$/       → translate_type + translate_message
/^[A-Za-z][A-Za-z0-9_.]+$/           → translate_type (bare, no message)
anything else                         → keep as-is
```

**`translate_message` targeted patterns** (run before fragment table):

```
"name 'X' is not defined"
    → "नाम 'X' परिभाषित नहीं है"

"'X' object has no attribute 'Y'"
    → "'X' वस्तु में विशेषता 'Y' नहीं है"

"f() takes N positional arguments but M were given"
    → "f() को N स्थितिगत तर्क चाहिए लेकिन M दिए गए"

"'X' object is not iterable/callable/subscriptable"
    → "'X' वस्तु दोहराने/कॉल/सब्स्क्रिप्ट योग्य नहीं है"

"unsupported operand type(s) for OP: 'X' and 'Y'"
    → "'X' और 'Y' के लिए OP संक्रिया असमर्थित है"

"invalid literal for int() with base N: 'X'"
    → "int() के लिए base N में 'X' अवैध अक्षर है"
```

**Test file**: `test/core/test_output_translator.py`

```
- translate_output: "True" → "सच" as whole word
- translate_output: "TrueValue" → "TrueValue" (not matched — not whole word)
- translate_output: "[True, False, None]" → "[सच, झूठ, कुछनहीं]"
- translate_type: all 35 error types return correct Hindi
- translate_type: unknown type returns original string unchanged
- translate_message: "name 'myVar' is not defined" → exact pattern match
- translate_message: "name 'अपरिभाषित' is not defined" → Hindi var name preserved
- translate_frame_line: correct फ़ाइल/पंक्ति/में substitution
- translate_error: पिछलावा present, Traceback absent
- translate_error: empty string → empty string returned
```

---

### Phase 1.7 — `core/hindi_parser.py`

**Single responsibility**: Extract identifiers from Hindi Python source
(after keyword restoration). Mirror of `parser.py` but skips
`REVERSE_BUILTIN_MAP` names instead of `BUILTIN_NAMES`.

**Public API**:

```python
def extract_hindi_identifiers(hindi_source: str) -> dict:
    """
    Called when user writes Hindi from scratch (no project.json exists).
    Restores keywords first, then walks AST.
    Returns same structure as extract_identifiers() in parser.py.

    Skips:
        - DUNDER names
        - Names in REVERSE_BUILTIN_MAP.keys() (already known Hindi builtins)
        - "स्वयं" (self equivalent)
    """
```

**Test file**: `test/core/test_hindi_parser.py`

```
- Basic Hindi function: extracts काम name, parameter names
- Skips छापो, योग, श्रेणी (they are in REVERSE_BUILTIN_MAP)
- Skips स्वयं
- Skips dunders
- Returns same dict structure as parser.py
```

---

### Phase 1.8 — `core/llm_reverse.py`

**Single responsibility**: Send Hindi identifiers to Sarvam LLM.
Return English translation map. Mirror of `llm_call.py`.

**Public API**:

```python
def reverse_translate_identifiers(flat_unique: list[str]) -> dict[str, str]:
    """
    Parameters:
        flat_unique: ["जोड़", "अ", "ब"]

    Returns:
        {"जोड़": "add", "अ": "a", "ब": "b"}

    Same error handling as llm_call.py.
    """
```

**System prompt behaviour**:

```
- Input:  JSON {"identifiers": ["जोड़", "छात्र", "अंक"]}
- Output: JSON {"जोड़": "add", "छात्र": "student", "अंक": "marks"}
- Output must be valid Python identifiers (snake_case, no spaces)
- No Devanagari in output values
- JSON only, no markdown, no explanation
```

**Test file**: `test/core/test_llm_reverse.py`

```
- Empty list: returns {} without API call
- Valid Hindi identifiers: all keys in response
- Output values are valid Python identifiers (re.match r'^[a-zA-Z_]\w*$')
- Missing key fallback: original Hindi fills missing (no KeyError downstream)
- Same error handling tests as test_llm_call.py (mocked)
```

---

### Phase 1 — End-to-End CLI Test

Add to `core/main.py` (not the web main):

```python
# core/main.py — CLI orchestrator, not the web app entry point

def translate_source(source: str, verbose: bool = True) -> tuple[str, dict]:
    """
    English source → (hindi_source, reverse_map)
    reverse_map includes both LLM translations and REVERSE_BUILTIN_MAP.
    """

def run_hindi_source(hindi_source: str, reverse_map: dict) -> tuple[str, str]:
    """
    Hindi source + reverse_map → (hindi_stdout, hindi_error)
    Thin wrapper over executor.execute_hindi_source().
    """

def run_hindi_file(filepath: str) -> tuple[str, str]:
    """
    Entry point for running a .py file written in Hindi.
    Loads project.json if exists (reverse_map).
    Falls back to hindi_parser + llm_reverse if not.
    """
```

---

## Phase 2 — Backend (FastAPI)

**Goal**: Expose Phase 1 pipeline as HTTP endpoints. Manage sessions.
Isolate execution via subprocess. All endpoints tested with FastAPI
`TestClient` in `test/backend/`.

**Complete when**: All `test/backend/` tests pass. Endpoints tested
with both valid and invalid inputs.

---

### Phase 2.1 — `backend/session.py`

**Single responsibility**: Store and retrieve session data in memory.
One session per browser tab identified by `session_id` (UUID).

```python
class SessionManager:
    """
    Stores per-session data:
        reverse_map:      dict[str, str]   Hindi→English identifier map
        translation_map:  dict[str, str]   English→Hindi identifier map
        hindi_source:     str              last translated Hindi source
        english_source:   str              last translated English source

    Methods:
        create() -> str                    generate UUID session_id
        get(session_id) -> dict | None     retrieve session data
        update(session_id, **kwargs)       merge new data into session
        delete(session_id)                 remove session
        cleanup_expired(max_age_seconds)   remove old sessions
    """
```

**Test file**: `test/backend/test_session.py`

```
- create() returns valid UUID string
- get() after create() returns empty dict
- update() merges data correctly
- get() nonexistent session_id returns None
- delete() removes session
- Two sessions are independent (no shared state)
```

---

### Phase 2.2 — `backend/sandbox.py`

**Single responsibility**: Execute English Python source in an isolated
subprocess with timeout. Never imports executor.py — subprocess isolation
means the child process imports it instead.

```python
def run_in_sandbox(
    english_source: str,
    timeout_seconds: int = 5,
) -> tuple[str, str]:
    """
    Runs english_source in a fresh subprocess.
    Returns (stdout, stderr).

    Implementation:
        subprocess.run(
            [sys.executable, "-c", english_source],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )

    On TimeoutExpired: return ("", "TimeoutError: execution exceeded 5s")
    On any other exception: return ("", f"SandboxError: {e}")

    Note: english_source must be fully restored English Python.
          The sandbox has no knowledge of Hindi.
    """
```

**Test file**: `test/backend/test_sandbox.py`

```
- Simple print: stdout="hello\n", stderr=""
- Arithmetic: correct result in stdout
- Timeout: returns TimeoutError message in stderr, empty stdout
- Infinite loop: caught by timeout
- SyntaxError in source: stderr contains error, stdout empty
- NameError: stderr contains error
- No import of project modules in child process (pure Python only)
```

---

### Phase 2.3 — `backend/routes/translate.py`

**Single responsibility**: Handle `/translate/*` endpoints. Calls Phase 1
core pipeline. Manages session via `SessionManager`.

```
POST /translate/to-hindi
    Body:    { "code": str, "session_id": str | null }
    Returns: {
        "hindi_code":       str,
        "session_id":       str,       ← created if null was passed
        "translation_map":  dict,
        "error":            str        ← "" on success
    }
    Behaviour:
        - If session_id null: create new session
        - Call core/main.translate_source(code)
        - Store reverse_map and translation_map in session
        - Return hindi_code and session_id

POST /translate/to-english
    Body:    { "code": str, "session_id": str }
    Returns: {
        "english_code": str,
        "error":        str
    }
    Behaviour:
        - Load reverse_map from session
        - If no session: call hindi_parser + llm_reverse
        - Run EnglishRestorer on the Hindi source
        - Return english_code
```

**Test file**: `test/backend/test_routes_translate.py`

```
- to-hindi valid code: 200, hindi_code present, session_id present
- to-hindi empty code: 422 validation error
- to-hindi null session_id: new session created, returned in response
- to-english valid: 200, english_code is valid Python (ast.parse succeeds)
- to-english missing session_id: 422
- to-english unknown session_id: 404
- to-hindi then to-english roundtrip: english_code ≈ original input
```

---

### Phase 2.4 — `backend/routes/execute.py`

**Single responsibility**: Handle `/execute/*` endpoints. Orchestrates
translation restoration and subprocess execution.

```
POST /execute/hindi
    Body:    { "code": str, "session_id": str }
    Returns: {
        "hindi_output":   str,
        "english_output": str,
        "hindi_error":    str,
        "english_error":  str,
        "success":        bool
    }
    Behaviour:
        - Load reverse_map from session
        - Call executor.execute_hindi_source() for Hindi output/error
        - Also run sandbox.run_in_sandbox(english_source) for English output
        - Return both outputs simultaneously

POST /execute/english
    Body:    { "code": str }
    Returns: {
        "output": str,
        "error":  str,
        "success": bool
    }
    Behaviour:
        - Call sandbox.run_in_sandbox(code) directly
        - No translation needed
```

**Test file**: `test/backend/test_routes_execute.py`

```
- execute/hindi success: hindi_output present, error empty, success=true
- execute/hindi NameError: hindi_error contains पिछलावा, success=false
- execute/hindi missing session: 404
- execute/hindi timeout (mock): hindi_error contains समयसीमा
- execute/english success: output present, error empty
- execute/english syntax error: error present, output empty
- Both panels populated simultaneously on success
```

---

### Phase 2.5 — `backend/app.py`

**Single responsibility**: FastAPI application factory. Mounts routes.
Serves static frontend files. Configures CORS.

```python
def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application.
    Called by uvicorn in production and by TestClient in tests.

    Includes:
        - /translate router
        - /execute router
        - StaticFiles mount for frontend/
        - CORS middleware (allow localhost:* in development)
        - /health endpoint for uptime checks
    """
```

---

## Phase 3 — Frontend

**Goal**: Two-panel CodeMirror editor with live sync, run button,
and bilingual output display. Vanilla JS only.

**Complete when**: Manual test checklist in `test/frontend/test_debounce.js`
passes in browser.

---

### Phase 3.1 — `frontend/hindi-mode.js`

**Single responsibility**: CodeMirror 6 language extension that highlights
Hindi Python keywords and builtins in the left panel.

```javascript
// Highlights these token types with CodeMirror theme variables:
//   Hindi keywords (काम, अगर, वरना...)  → cm-keyword color
//   Hindi builtins (छापो, लंबाई...)     → cm-builtin color
//   String literals                      → cm-string color
//   Numbers                              → cm-number color
//   Comments (# ...)                     → cm-comment color
//   Operators                            → cm-operator color

// Uses StreamLanguage or LezerParser depending on complexity.
// Minimum viable: StreamLanguage with token() function.
```

---

### Phase 3.2 — `frontend/api.js`

**Single responsibility**: Typed fetch wrappers for all backend endpoints.
Never touches the DOM.

```javascript
const API_BASE = "http://localhost:8000";

async function translateToHindi(code, sessionId)   → { hindiCode, sessionId, error }
async function translateToEnglish(code, sessionId) → { englishCode, error }
async function executeHindi(code, sessionId)        → { hindiOutput, englishOutput,
                                                        hindiError, englishError, success }
async function executeEnglish(code)                 → { output, error, success }

// All functions:
//   - Set Content-Type: application/json
//   - Throw descriptive Error on non-2xx response
//   - Return parsed JSON on success
```

---

### Phase 3.3 — `frontend/editor.js`

**Single responsibility**: Panel setup, debounce logic, sync lock,
run button, output display. Imports from api.js.

**State managed**:

```javascript
let sessionId     = null;    // set after first translation
let syncLock      = false;   // prevents panels triggering each other
let debounceTimer = null;    // setTimeout handle

// Debounce rules:
//   - User types in left (Hindi) panel:
//       clear debounceTimer
//       set debounceTimer = setTimeout(syncToEnglish, 800)
//   - User types in right (English) panel:
//       clear debounceTimer
//       set debounceTimer = setTimeout(syncToHindi, 800)
//   - syncLock prevents the updated panel from triggering back

// syncToHindi():
//   syncLock = true
//   result = await translateToHindi(leftPanel.value, sessionId)
//   sessionId = result.sessionId
//   rightPanel.value = result.englishCode   ← wait, this is backwards
//   Actually: leftPanel has Hindi, rightPanel has English
//   translateToHindi sends English → gets Hindi → updates leftPanel
//   translateToEnglish sends Hindi → gets English → updates rightPanel

// Run button:
//   disable button, show spinner
//   result = await executeHindi(leftPanel.value, sessionId)
//   hindiOutputPanel.textContent = result.hindiOutput || result.hindiError
//   englishOutputPanel.textContent = result.englishOutput || result.englishError
//   re-enable button
```

---

### Phase 3.4 — `frontend/index.html` + `frontend/style.css`

**Layout**:

```
┌─────────────────────────────────────────────────────────────┐
│  🔵 हिंदी Python Playground                    [dark/light] │
├──────────────────────────┬──────────────────────────────────┤
│  Hindi Panel             │  English Panel                   │
│  [CodeMirror editor]     │  [CodeMirror editor]             │
│                          │                                  │
│  800px min-height        │  800px min-height                │
│  Noto Sans Devanagari    │  JetBrains Mono / Courier        │
├──────────────────────────┴──────────────────────────────────┤
│  [ ▶ चलाओ / Run ]   [ ⟳ Reset ]   [ ↔ Sync ]   [● Ready] │
├──────────────────────────┬──────────────────────────────────┤
│  Hindi Output            │  English Output                  │
│  terminal style          │  terminal style                  │
│  green text on success   │  green text on success           │
│  red text on error       │  red text on error               │
└──────────────────────────┴──────────────────────────────────┘
```

**Fonts**:

```css
.hindi-panel { font-family: 'Noto Sans Devanagari', monospace; }
.english-panel { font-family: 'JetBrains Mono', 'Courier New', monospace; }
.output-panel  { font-family: 'JetBrains Mono', monospace; line-height: 1.6; }
.hindi-output  { color: #4ade80; }   /* green */
.error-output  { color: #f87171; }   /* red   */
```

---

### Phase 3 — Frontend Manual Test Checklist

**File**: `test/frontend/test_debounce.js` — open in browser console.

```
□ Type in left (Hindi) panel → right panel updates after 800ms
□ Type in right (English) panel → left panel updates after 800ms
□ Rapid typing in left → only ONE API call made (debounce working)
□ syncLock prevents echo: updating right panel does not re-trigger left
□ Run button disabled during execution
□ Run button re-enabled after execution completes
□ Success: both output panels show output
□ Error: both panels show error in respective language
□ Hindi error contains पिछलावा, not "Traceback"
□ Reset clears both editors and both output panels
□ Dark/light mode toggle works
□ Page works on mobile viewport (responsive layout)
□ Noto Sans Devanagari loaded (check Network tab)
□ No CORS errors in console
□ session_id persists across multiple runs (check localStorage or memory)
```

---

## Environment Setup

```bash
# Install uv if not present
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project
uv init hindi-playground
cd hindi-playground

# Add dependencies
uv add fastapi uvicorn python-dotenv sarvamai

# Add dev dependencies
uv add --dev pytest pytest-asyncio httpx

# Environment variables
cp .env.example .env
# Edit .env and add your key:
# SARVAM_API=sk_...

# Run all core tests
uv run pytest test/core/ -v

# Run all backend tests
uv run pytest test/backend/ -v

# Start the server
uv run uvicorn backend.app:create_app --factory --reload --port 8000

# Open frontend
open frontend/index.html
# or serve via FastAPI static files at http://localhost:8000
```

---

## `.env.example`

```
SARVAM_API=sk_your_key_here
SESSION_MAX_AGE_SECONDS=3600
EXECUTION_TIMEOUT_SECONDS=5
DEBUG=true
```

---

## Testing Strategy

```
test/core/          Unit tests — no API calls (mock llm_call and llm_reverse)
                    No FastAPI, no browser, no subprocess
                    Run with: uv run pytest test/core/ -v

test/backend/       Integration tests — real FastAPI via TestClient
                    Mock sandbox.run_in_sandbox for execution tests
                    Mock llm_call for translation tests
                    Run with: uv run pytest test/backend/ -v

test/frontend/      Manual checklist — run in browser
                    No automated framework (Playwright optional in future)
```

**Mocking convention** — use `unittest.mock.patch` consistently:

```python
# In test/core/test_llm_call.py
from unittest.mock import patch, MagicMock

def test_valid_translation():
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"greet":"स्वागत"}'
    mock_response.choices[0].finish_reason = "stop"

    with patch("core.llm_call.client") as mock_client:
        mock_client.chat.completions.return_value = mock_response
        result = translate_identifiers(["greet"])
        assert result == {"greet": "स्वागत"}
```

---

## Phase Completion Checklist

### Phase 1 — Core
```
□ constants.py — all tables defined, reverse maps derived
□ parser.py — extract_identifiers() passes all 9 tests
□ llm_call.py — translate_identifiers() passes all 8 tests
□ unparser.py — HindiUnparser passes all 12 tests
□ executor.py — passes all success tests and all error tests
□ output_translator.py — passes all 10 tests
□ hindi_parser.py — passes all 4 tests
□ llm_reverse.py — passes all 6 tests
□ core/main.py CLI — end-to-end: English file → Hindi output → execute
□ uv run pytest test/core/ -v → all green
```

### Phase 2 — Backend
```
□ session.py — SessionManager passes all 6 tests
□ sandbox.py — subprocess isolation passes all 7 tests
□ routes/translate.py — all 7 route tests pass
□ routes/execute.py — all 6 route tests pass
□ app.py — /health returns 200, static files served
□ uv run pytest test/backend/ -v → all green
□ Manual: curl all endpoints from terminal
```

### Phase 3 — Frontend
```
□ hindi-mode.js — Hindi keywords highlighted in left panel
□ api.js — all fetch wrappers return correct shapes
□ editor.js — debounce working (verified with Network tab)
□ syncLock working (no echo loop)
□ Run button states working
□ Both output panels populated on execute
□ test/frontend/test_debounce.js checklist — all boxes checked
□ Works on Chrome, Firefox, Safari
```

---

## Common Pitfalls — Read Before Coding

**`textwrap.dedent()` before `ast.parse()`** — always strip common leading
whitespace from triple-quoted test strings or you get `IndentationError`.

**`ast.fix_missing_locations()`** — required after any `ast.NodeTransformer`
visit. Without it `ast.unparse()` raises `TypeError` on nodes missing `lineno`.

**Leading underscore methods on `NodeTransformer` subclasses** — do not name
methods `_rename` or `_translate` on classes that extend AST base classes.
Use `rename`, `translate` without the underscore.

**`globals_` parameter name** — do not use trailing underscore on function
parameters. Rename to `exec_globals` to avoid CPython 3.13 scope issues.

**`import traceback as tb`** — always alias. A bare `traceback` name in
`except` blocks will shadow correctly if imported, but `tb` makes the alias
explicit and avoids the common missing-import error.

**Sarvam `reasoning_effort=None`** — always pass explicitly. Default is `"low"`
which consumes tokens for internal reasoning, leaving nothing for `content`.

**`BUILTIN_MAP` wins over LLM** — always merge as `{**translation_map, **BUILTIN_MAP}`
so builtins on the right side overwrite any LLM translation of the same name.

**`elif` in AST is not a node** — `elif` is represented as `orelse=[ast.If(...)]`.
The `visit_If` method must detect this pattern with a `while` loop to emit
`नहींतो` correctly instead of a nested `अगर`/`वरना` block.

**Devanagari word boundaries** — `\b` in regex does not work with Unicode.
Use `(?<![a-zA-Z\u0900-\u097F_])keyword(?![a-zA-Z\u0900-\u097F_])` for
all Hindi keyword substitutions.
