// Pure data — no editor-library imports.
// Consumed by editor.js (Monaco token colors) and hindi-mode.js (tokenizer vocabulary).

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

export const HINDI_KEYWORDS  = new Set(Object.values(KEYWORD_MAP));
export const HINDI_BUILTINS  = new Set(Object.values(BUILTIN_MAP));
export const HINDI_CONSTANTS = new Set(Object.values(CONSTANT_MAP));
export const ENGLISH_BUILTINS = new Set(Object.keys(BUILTIN_MAP));

// CSS-variable color tokens — same names as style.css --cm-* props.
// editor.js reads these to build Monaco theme rules; style.css owns the
// actual hex values so light/dark toggling stays in one place.
// Monaco themes require literal color strings, so we resolve the CSS vars
// at runtime from a temporary element rather than hardcoding hex here.
export function resolveCssVar(name) {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
}
