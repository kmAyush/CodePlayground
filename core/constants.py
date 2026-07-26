"""Static lookup tables for English <-> Hindi Python translation.

Zero logic. Zero imports from within the project.
"""

KEYWORD_MAP: dict[str, str] = {
    "def": "काम",
    "if": "अगर",
    "elif": "नहींतो",
    "else": "वरना",
    "for": "केलिए",
    "while": "जबतक",
    "in": "में",
    "class": "क्लास",
    "try": "कोशिश",
    "except": "सिवाय",
    "finally": "अंत_में",
    "return": "वापस",
    "import": "आयात",
    "from": "से",
    "as": "जैसे",
    "pass": "पास",
    "break": "रुको",
    "continue": "जारी",
    "global": "वैश्विक",
    "nonlocal": "गैरस्थानीय",
    "lambda": "लैम्ब्डा",
    "raise": "उठाओ",
    "assert": "पुष्टि",
    "del": "हटाओ",
    "with": "साथ",
    "yield": "उत्पन्न",
    "async": "असिंक",
    "await": "प्रतीक्षा",
    "and": "और",
    "or": "या",
    "not": "नहीं",
    "is": "है",
}

BUILTIN_MAP: dict[str, str] = {
    "print": "छापो",
    "len": "लंबाई",
    "range": "श्रेणी",
    "input": "इनपुट",
    "int": "पूर्णांक",
    "float": "दशमलव",
    "str": "स्ट्रिंग",
    "bool": "बूलियन",
    "list": "सूची",
    "dict": "शब्दकोश",
    "set": "समुच्चय",
    "tuple": "टपल",
    "type": "प्रकार",
    "sum": "योग",
    "max": "अधिकतम",
    "min": "न्यूनतम",
    "abs": "निरपेक्ष",
    "round": "पूर्णांकित",
    "sorted": "क्रमबद्ध",
    "reversed": "उल्टा",
    "enumerate": "गणना",
    "zip": "जिप",
    "map": "मैप",
    "filter": "फ़िल्टर",
    "open": "खोलो",
    "isinstance": "प्रकार_जांच",
    "super": "सुपर",
    "id": "पहचान",
    "hash": "हैश",
    "next": "अगला",
    "iter": "पुनरावर्तक",
    "format": "प्रारूप",
    "repr": "रिप्र",
    "ord": "ऑर्ड",
    "chr": "अक्षर",
    "all": "सभी",
    "any": "कोई",
    "object": "वस्तु",
}

BUILTIN_NAMES: set[str] = set(BUILTIN_MAP.keys())

# Populate to keep specific methods in English display.
BUILTIN_METHODS: set[str] = set()

REVERSE_BUILTIN_MAP: dict[str, str] = {v: k for k, v in BUILTIN_MAP.items()}

OUTPUT_MAP: dict[str, str] = {
    "True": "सच",
    "False": "झूठ",
    "None": "कुछनहीं",
}

ERROR_TYPE_MAP: dict[str, str] = {
    "NameError": "नाम_त्रुटि",
    "TypeError": "प्रकार_त्रुटि",
    "ValueError": "मान_त्रुटि",
    "ZeroDivisionError": "शून्य_भाग_त्रुटि",
    "IndexError": "अनुक्रमणिका_त्रुटि",
    "KeyError": "कुंजी_त्रुटि",
    "AttributeError": "विशेषता_त्रुटि",
    "RecursionError": "पुनरावर्तन_त्रुटि",
    "ImportError": "आयात_त्रुटि",
    "ModuleNotFoundError": "मॉड्यूल_त्रुटि",
    "FileNotFoundError": "फ़ाइल_त्रुटि",
    "FileExistsError": "फ़ाइल_उपस्थित_त्रुटि",
    "IsADirectoryError": "निर्देशिका_त्रुटि",
    "NotADirectoryError": "गैर_निर्देशिका_त्रुटि",
    "IOError": "इनपुट_आउटपुट_त्रुटि",
    "OSError": "तंत्र_त्रुटि",
    "StopIteration": "पुनरावृत्ति_समाप्ति",
    "StopAsyncIteration": "असिंक_पुनरावृत्ति_समाप्ति",
    "SyntaxError": "वाक्य_रचना_त्रुटि",
    "IndentationError": "हाशिया_त्रुटि",
    "TabError": "टैब_त्रुटि",
    "RuntimeError": "रनटाइम_त्रुटि",
    "NotImplementedError": "अकार्यान्वित_त्रुटि",
    "OverflowError": "अतिप्रवाह_त्रुटि",
    "FloatingPointError": "दशमलव_बिंदु_त्रुटि",
    "UnboundLocalError": "अबद्ध_स्थानीय_त्रुटि",
    "AssertionError": "पुष्टि_त्रुटि",
    "ArithmeticError": "अंकगणित_त्रुटि",
    "BufferError": "बफर_त्रुटि",
    "EOFError": "फ़ाइल_अंत_त्रुटि",
    "MemoryError": "स्मृति_त्रुटि",
    "ReferenceError": "संदर्भ_त्रुटि",
    "UnicodeError": "यूनिकोड_त्रुटि",
    "PermissionError": "अनुमति_त्रुटि",
    "TimeoutError": "समयसीमा_त्रुटि",
}

# Ordered longest-fragment-first English -> Hindi substrings for
# translate_message() fallback substitution.
ERROR_MSG_MAP: list[tuple[str, str]] = sorted(
    [
        ("object has no attribute", "वस्तु में विशेषता नहीं है"),
        ("list index out of range", "सूची अनुक्रमणिका सीमा से बाहर"),
        ("index out of range", "अनुक्रमणिका सीमा से बाहर"),
        ("takes no arguments", "कोई तर्क नहीं लेता"),
        ("positional argument", "स्थितिगत तर्क"),
        ("keyword argument", "कीवर्ड तर्क"),
        ("division by zero", "शून्य से भाग"),
        ("is not defined", "परिभाषित नहीं है"),
        ("is not callable", "कॉल योग्य नहीं है"),
        ("is not iterable", "दोहराने योग्य नहीं है"),
        ("is not subscriptable", "सब्स्क्रिप्ट योग्य नहीं है"),
        ("unsupported operand", "असमर्थित संक्रिया"),
        ("must be str", "स्ट्रिंग होना चाहिए"),
        ("invalid literal", "अवैध अक्षर"),
        ("not enough values", "पर्याप्त मान नहीं"),
        ("no attribute", "कोई विशेषता नहीं"),
    ],
    key=lambda pair: len(pair[0]),
    reverse=True,
)
TRACEBACK_WORD: str = "पिछलावा"


def DUNDER(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")
