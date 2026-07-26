// CodeMirror 6 language extension that highlights Hindi Python source in
// the left panel: keywords, builtins, function/class definitions, string
// literals, numbers, comments, decorators, attribute access and operators.
// Never touches the DOM.
//
// Bare specifier imports — resolved via the importmap in index.html.
// See theme.js for why bare specifiers are required here.

import { StreamLanguage, syntaxHighlighting } from "@codemirror/language";
import { tags as t } from "@lezer/highlight";
import {
  KEYWORD_MAP,
  HINDI_KEYWORDS,
  HINDI_BUILTINS,
  HINDI_CONSTANTS,
  pythonHighlightStyle,
} from "./theme.js";

const DEF_WORD = KEYWORD_MAP.def;
const CLASS_WORD = KEYWORD_MAP.class;

// Mirrors the backend's Unicode-aware identifier boundary
// (?<![a-zA-Zऀ-ॿ_]) used in core/executor.py's restore_keywords.
const WORD_RE = /^[A-Za-z_ऀ-ॿ][A-Za-z0-9_ऀ-ॿ]*/;
const NUMBER_RE = /^\d+\.?\d*/;
const OPERATOR_RE = /^(?:\*\*|\/\/|==|!=|<=|>=|->|[+\-*/%=<>!&|^~@:])/;
const PUNCTUATION_RE = /^[()[\]{},]/;

function stringTokenizer(quote) {
  return function token(stream, state) {
    let escaped = false;
    let ch;
    while ((ch = stream.next()) != null) {
      if (ch === quote && !escaped) break;
      escaped = !escaped && ch === "\\";
    }
    state.tokenize = tokenBase;
    return "string";
  };
}

function tripleStringTokenizer(quote) {
  return function token(stream, state) {
    while (!stream.eol()) {
      if (stream.match(quote)) {
        state.tokenize = tokenBase;
        return "string";
      }
      stream.next();
    }
    return "string";
  };
}

function tokenBase(stream, state) {
  // Track whether the *next real token* is at the start of a line so the
  // decorator "@" check works correctly even after leading indentation.
  // sol() is true only at character position 0 of a line. Once eatSpace()
  // advances past the indent, sol() returns false on the next call.
  // We preserve freshLine across the whitespace-only call so the first real
  // token still sees isLineStart = true, then clear it so later tokens on
  // the same line don't incorrectly think they are at line start.
  if (stream.sol()) state.freshLine = true;

  if (stream.eatSpace()) {
    // Do NOT clear freshLine here — carry it forward to the next call so
    // the first real token after indentation is still treated as line-start.
    return null;
  }

  const isLineStart = state.freshLine;
  state.freshLine = false; // consumed: remaining tokens on this line are not at start
  const afterDot = state.afterDot;
  state.afterDot = false;

  if (stream.match("#")) {
    stream.skipToEnd();
    return "comment";
  }

  // Decorators ("@काम_सज्जाकार" etc) only make sense at the start of a
  // statement — elsewhere "@" is the matrix-multiplication operator.
  if (isLineStart && stream.peek() === "@") {
    stream.skipToEnd();
    return "decorator";
  }

  if (stream.match('"""') || stream.match("'''")) {
    const quote = stream.current();
    state.tokenize = tripleStringTokenizer(quote);
    return state.tokenize(stream, state);
  }

  const ch = stream.peek();
  if (ch === '"' || ch === "'") {
    stream.next();
    state.tokenize = stringTokenizer(ch);
    return state.tokenize(stream, state);
  }

  if (stream.match(NUMBER_RE)) return "number";

  if (stream.match(WORD_RE)) {
    const word = stream.current();

    // The identifier right after काम/class is the definition's own name,
    // not a reference — color it like a def, not a plain variable.
    if (state.expectDefName) {
      const kind = state.expectDefName;
      state.expectDefName = null;
      return kind === "class" ? "className" : "functionName";
    }

    if (word === DEF_WORD) {
      state.expectDefName = "function";
      return "keyword";
    }
    if (word === CLASS_WORD) {
      state.expectDefName = "class";
      return "keyword";
    }
    if (HINDI_KEYWORDS.has(word)) return "keyword";
    if (HINDI_CONSTANTS.has(word)) return "constant";
    if (afterDot) return "property";
    if (HINDI_BUILTINS.has(word)) return "builtin";
    if (stream.peek() === "(") return "functionCall";
    return "variable";
  }

  if (stream.match(".")) {
    state.afterDot = true;
    return "punctuation";
  }

  if (stream.match(OPERATOR_RE)) return "operator";

  if (stream.match(PUNCTUATION_RE)) return "punctuation";

  stream.next();
  return null;
}

const tokenTable = {
  keyword: t.keyword,
  builtin: t.standard(t.name),
  functionName: t.function(t.definition(t.variableName)),
  functionCall: t.function(t.variableName),
  className: t.definition(t.className),
  property: t.propertyName,
  constant: t.atom,
  decorator: t.meta,
  string: t.string,
  number: t.number,
  comment: t.lineComment,
  operator: t.operator,
  punctuation: t.punctuation,
  variable: t.variableName,
};

const hindiLanguage = StreamLanguage.define({
  token: (stream, state) => state.tokenize(stream, state),
  startState: () => ({
    tokenize: tokenBase,
    freshLine: true,
    afterDot: false,
    expectDefName: null,
  }),
  tokenTable,
  languageData: {
    commentTokens: { line: "#" },
  },
});

export function hindiSupport() {
  return [hindiLanguage, syntaxHighlighting(pythonHighlightStyle)];
}

export { hindiLanguage };
