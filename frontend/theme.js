// Shared nvim-like syntax highlighting for both editors: one HighlightStyle,
// one set of CSS variables (see style.css) — a token category (keyword,
// function, string, ...) renders in the same color whether it's read from
// the English panel (real Python grammar via @codemirror/lang-python) or
// the Hindi panel (custom tokenizer in hindi-mode.js). Never touches the DOM
// beyond the decorations CodeMirror itself manages.
//
// Bare specifier imports — resolved via the importmap in index.html to exact
// pinned versions. Every file on this page must use bare specifiers (never
// full esm.sh URLs) so the browser module cache de-duplicates correctly.
// Tag objects from @lezer/highlight are compared by identity; two instances
// from different URL strings means HighlightStyle silently matches nothing.

import { HighlightStyle, syntaxTree } from "@codemirror/language";
import { tags as t } from "@lezer/highlight";
import { ViewPlugin, Decoration, MatchDecorator } from "@codemirror/view";

// Python keyword/builtin vocabulary, mirrored from core/constants.py.
export const KEYWORD_MAP = {
  def: "काम",
  if: "अगर",
  elif: "नहींतो",
  else: "वरना",
  for: "केलिए",
  while: "जबतक",
  in: "में",
  class: "क्लास",
  try: "कोशिश",
  except: "सिवाय",
  finally: "अंत_में",
  return: "वापस",
  import: "आयात",
  from: "से",
  as: "जैसे",
  pass: "पास",
  break: "रुको",
  continue: "जारी",
  global: "वैश्विक",
  nonlocal: "गैरस्थानीय",
  lambda: "लैम्ब्डा",
  raise: "उठाओ",
  assert: "पुष्टि",
  del: "हटाओ",
  with: "साथ",
  yield: "उत्पन्न",
  async: "असिंक",
  await: "प्रतीक्षा",
  and: "और",
  or: "या",
  not: "नहीं",
  is: "है",
};

export const BUILTIN_MAP = {
  print: "छापो",
  len: "लंबाई",
  range: "श्रेणी",
  input: "इनपुट",
  int: "पूर्णांक",
  float: "दशमलव",
  str: "स्ट्रिंग",
  bool: "बूलियन",
  list: "सूची",
  dict: "शब्दकोश",
  set: "समुच्चय",
  tuple: "टपल",
  type: "प्रकार",
  sum: "योग",
  max: "अधिकतम",
  min: "न्यूनतम",
  abs: "निरपेक्ष",
  round: "पूर्णांकित",
  sorted: "क्रमबद्ध",
  reversed: "उल्टा",
  enumerate: "गणना",
  zip: "जिप",
  map: "मैप",
  filter: "फ़िल्टर",
  open: "खोलो",
  isinstance: "प्रकार_जांच",
  super: "सुपर",
  id: "पहचान",
  hash: "हैश",
  next: "अगला",
  iter: "पुनरावर्तक",
  format: "प्रारूप",
  repr: "रिप्र",
  ord: "ऑर्ड",
  chr: "अक्षर",
  all: "सभी",
  any: "कोई",
  object: "वस्तु",
};

export const CONSTANT_MAP = { True: "सच", False: "झूठ", None: "कुछनहीं" };

export const HINDI_KEYWORDS = new Set(Object.values(KEYWORD_MAP));
export const HINDI_BUILTINS = new Set(Object.values(BUILTIN_MAP));
export const HINDI_CONSTANTS = new Set(Object.values(CONSTANT_MAP));
export const ENGLISH_BUILTINS = new Set(Object.keys(BUILTIN_MAP));

// One color per token category, shared by both languages. Actual hex
// values live in style.css as --cm-* custom properties so the existing
// light/dark toggle applies to code coloring automatically.
export const pythonHighlightStyle = HighlightStyle.define([
  {
    tag: [t.keyword, t.controlKeyword, t.operatorKeyword, t.moduleKeyword, t.definitionKeyword],
    color: "var(--cm-keyword)",
    fontWeight: "600",
  },
  {
    tag: [
      t.function(t.variableName),
      t.function(t.definition(t.variableName)),
      t.definition(t.function(t.variableName)),
    ],
    color: "var(--cm-function)",
  },
  { tag: t.standard(t.name), color: "var(--cm-builtin)" },
  { tag: [t.className, t.definition(t.className)], color: "var(--cm-class)" },
  { tag: [t.propertyName, t.definition(t.propertyName)], color: "var(--cm-property)" },
  { tag: [t.bool, t.null, t.atom], color: "var(--cm-constant)" },
  { tag: t.string, color: "var(--cm-string)" },
  { tag: [t.number, t.integer, t.float], color: "var(--cm-number)" },
  {
    tag: [t.comment, t.lineComment, t.blockComment, t.docComment],
    color: "var(--cm-comment)",
    fontStyle: "italic",
  },
  { tag: t.meta, color: "var(--cm-decorator)", fontStyle: "italic" },
  { tag: t.operator, color: "var(--cm-operator)" },
  { tag: [t.punctuation, t.bracket, t.separator], color: "var(--cm-punctuation)" },
  { tag: t.variableName, color: "var(--cm-variable)" },
]);

function escapeRegExp(word) {
  return word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// The real Python grammar (@codemirror/lang-python) has no notion of
// "builtin" — print/len/range parse as plain function calls, same as any
// user-defined name. This decorates whole-word matches of known builtin
// names with --cm-builtin so the English panel's builtins match color with
// the Hindi panel's (which the hand-written tokenizer already tags natively).
export function highlightBuiltins(names) {
  const pattern = new RegExp(`\\b(?:${[...names].map(escapeRegExp).join("|")})\\b`, "g");
  const matcher = new MatchDecorator({
    regexp: pattern,
    decoration: (_match, view, pos) => {
      const node = syntaxTree(view.state).resolveInner(pos, 1);
      if (node.name !== "VariableName") return null;
      return Decoration.mark({ attributes: { style: "color: var(--cm-builtin)" } });
    },
  });
  return ViewPlugin.define(
    (view) => ({
      decorations: matcher.createDeco(view),
      update(update) {
        this.decorations = matcher.updateDeco(update, this.decorations);
      },
    }),
    { decorations: (v) => v.decorations }
  );
}
