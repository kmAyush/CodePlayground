// Monaco language definition for Hindi Python.
// Registers a tokenizer with Monaco's Monarch engine — a simple declarative
// regex-rule system, no StreamLanguage / lezer involved.
// Called once after Monaco is loaded, before the Hindi editor is created.

import { KEYWORD_MAP, BUILTIN_MAP, CONSTANT_MAP } from "./theme.js";

const HINDI_KEYWORDS  = Object.values(KEYWORD_MAP);
const HINDI_BUILTINS  = Object.values(BUILTIN_MAP);
const HINDI_CONSTANTS = Object.values(CONSTANT_MAP);

export const HINDI_LANG_ID = "hindi-python";

export function registerHindiLanguage() {
  const monaco = window.monaco;

  monaco.languages.register({ id: HINDI_LANG_ID });

  // Monarch tokenizer — rules run top-to-bottom per line.
  // Unicode word chars cover the Devanagari block (U+0900–U+097F ⊂ ऀ–ॿ).
  monaco.languages.setMonarchTokensProvider(HINDI_LANG_ID, {
    keywords:  HINDI_KEYWORDS,
    builtins:  HINDI_BUILTINS,
    constants: HINDI_CONSTANTS,

    // identifier: ASCII + Devanagari letters, digits, underscore
    identifier: /[A-Za-z_\u0900-\u097F][A-Za-z0-9_\u0900-\u097F]*/,

    tokenizer: {
      root: [
        // Single-line comment
        [/#.*$/, "comment"],

        // Decorator (@ at start of non-whitespace on a line)
        [/^\s*@[^\n]*/, "decorator"],

        // Triple-quoted strings — switch to embedded state
        [/"""/, { token: "string", next: "@tripleDoubleString" }],
        [/'''/, { token: "string", next: "@tripleSingleString" }],

        // Single-quoted strings
        [/"([^"\\]|\\.)*"/, "string"],
        [/'([^'\\]|\\.)*'/, "string"],

        // Numbers
        [/\d+\.?\d*/, "number"],

        // Identifiers → classify as keyword / constant / builtin / plain
        [
          /[A-Za-z_\u0900-\u097F][A-Za-z0-9_\u0900-\u097F]*/,
          {
            cases: {
              "@keywords":  "keyword",
              "@constants": "constant",
              "@builtins":  "builtin",
              "@default":   "identifier",
            },
          },
        ],

        // Operators
        [/[+\-*/%=<>!&|^~@:]+/, "operator"],

        // Punctuation / brackets
        [/[()[\]{},.]/, "delimiter"],

        // Whitespace
        [/\s+/, "white"],
      ],

      tripleDoubleString: [
        [/"""/, { token: "string", next: "@pop" }],
        [/./, "string"],
      ],

      tripleSingleString: [
        [/'''/, { token: "string", next: "@pop" }],
        [/./, "string"],
      ],
    },
  });

  // Language config: brackets, auto-close, indentation comment token
  monaco.languages.setLanguageConfiguration(HINDI_LANG_ID, {
    comments: { lineComment: "#" },
    brackets: [["(", ")"], ["[", "]"], ["{", "}"]],
    autoClosingPairs: [
      { open: "(", close: ")" },
      { open: "[", close: "]" },
      { open: "{", close: "}" },
      { open: '"', close: '"', notIn: ["string"] },
      { open: "'", close: "'", notIn: ["string"] },
    ],
    indentationRules: {
      increaseIndentPattern: /:\s*(#.*)?$/,
      decreaseIndentPattern: /^\s*(वरना|नहींतो|सिवाय|अंत_में|else|elif|except|finally)\b/,
    },
  });
}
