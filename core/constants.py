"""Static lookup tables for English <-> Hindi Python translation.

Zero logic. Zero imports from within the project.
"""

KEYWORD_MAP: dict[str, str] = {
    "def": "kaam",
    "if": "agar",
    "elif": "nahi_toh",
    "else": "varna",
    "for": "dohrayo",
    "while": "jabtab",
    "in": "mein",
    "class": "class",
    "try": "koshish",
    "except": "siwaye",
    "finally": "aant_mein",
    "return": "vaapas",
    "import": "bharti",
    "from": "se",
    "as": "jaise",
    "pass": "pass",
    "break": "ruko",
    "continue": "jaari",
    "global": "vaishvik",
    "nonlocal": "gairsthaniyay",
    "lambda": "lambda",
    "raise": "uthayo",
    "assert": "pushti",
    "del": "hatao",
    "with": "saath",
    "yield": "utpann",
    "async": "async",
    "await": "prateeksha",
    "and": "aur",
    "or": "ya",
    "not": "nahi",
    "is": "hai",
}

BUILTIN_MAP: dict[str, str] = {
    "print": "chhapo",
    "len": "lambai",
    "range": "shreni",
    "input": "input",
    "int": "purnank",
    "float": "dashamlav",
    "str": "string",
    "bool": "boolean",
    "list": "suchi",
    "dict": "shabdkosh",
    "set": "samuchay",
    "tuple": "tapal",
    "type": "prakar",
    "sum": "yog",
    "max": "adhiktam",
    "min": "nyuntam",
    "abs": "nirapeksh",
    "round": "purnankit",
    "sorted": "kramabaddh",
    "reversed": "ulta",
    "enumerate": "ganana",
    "zip": "zip",
    "map": "map",
    "filter": "filter",
    "open": "kholo",
    "isinstance": "prakar_jaanch",
    "super": "super",
    "id": "pehchaan",
    "hash": "hash",
    "next": "agla",
    "iter": "punaravartak",
    "format": "praroop",
    "repr": "ripr",
    "ord": "ord",
    "chr": "akshar",
    "all": "sabhi",
    "any": "koi",
    "object": "vastu",
}

BUILTIN_NAMES: set[str] = set(BUILTIN_MAP.keys())

# Populate to keep specific methods in English display.
BUILTIN_METHODS: set[str] = set()

REVERSE_BUILTIN_MAP: dict[str, str] = {v: k for k, v in BUILTIN_MAP.items()}

OUTPUT_MAP: dict[str, str] = {
    "True": "sach",
    "False": "jhooth",
    "None": "kuchhnahi",
}

ERROR_TYPE_MAP: dict[str, str] = {
    "NameError": "naam_truti",
    "TypeError": "prakar_truti",
    "ValueError": "maan_truti",
    "ZeroDivisionError": "shunya_bhaag_truti",
    "IndexError": "anukramanika_truti",
    "KeyError": "kunji_truti",
    "AttributeError": "visheshta_truti",
    "RecursionError": "punaravartan_truti",
    "ImportError": "bharti_truti",
    "ModuleNotFoundError": "module_truti",
    "FileNotFoundError": "file_truti",
    "FileExistsError": "file_upasthit_truti",
    "IsADirectoryError": "nirdeshika_truti",
    "NotADirectoryError": "gair_nirdeshika_truti",
    "IOError": "input_output_truti",
    "OSError": "tantra_truti",
    "StopIteration": "punaravritti_samaapti",
    "StopAsyncIteration": "async_punaravritti_samaapti",
    "SyntaxError": "vaakya_rachna_truti",
    "IndentationError": "haashiya_truti",
    "TabError": "tab_truti",
    "RuntimeError": "runtime_truti",
    "NotImplementedError": "akaaryaanvit_truti",
    "OverflowError": "atipravaah_truti",
    "FloatingPointError": "dashamlav_bindu_truti",
    "UnboundLocalError": "abaddh_sthaaniya_truti",
    "AssertionError": "pushti_truti",
    "ArithmeticError": "ankganit_truti",
    "BufferError": "buffer_truti",
    "EOFError": "file_ant_truti",
    "MemoryError": "smriti_truti",
    "ReferenceError": "sandarbh_truti",
    "UnicodeError": "unicode_truti",
    "PermissionError": "anumati_truti",
    "TimeoutError": "samay_seema_truti",
}

# Ordered longest-fragment-first English -> Hindi substrings for
# translate_message() fallback substitution.
ERROR_MSG_MAP: list[tuple[str, str]] = sorted(
    [
        ("object has no attribute", "vastu mein visheshta nahi hai"),
        ("list index out of range", "suchi anukramanika seema se baahar"),
        ("index out of range", "anukramanika seema se baahar"),
        ("takes no arguments", "koi tark nahi leta"),
        ("positional argument", "sthitigat tark"),
        ("keyword argument", "keyword tark"),
        ("division by zero", "shunya se bhaag"),
        ("is not defined", "paribhashit nahi hai"),
        ("is not callable", "call yogya nahi hai"),
        ("is not iterable", "dohrane yogya nahi hai"),
        ("is not subscriptable", "subscript yogya nahi hai"),
        ("unsupported operand", "asamarthit sankriya"),
        ("must be str", "string hona chahiye"),
        ("invalid literal", "avaidh akshar"),
        ("not enough values", "paryapt maan nahi"),
        ("no attribute", "koi visheshta nahi"),
    ],
    key=lambda pair: len(pair[0]),
    reverse=True,
)
TRACEBACK_WORD: str = "Jaanch"


def DUNDER(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")
