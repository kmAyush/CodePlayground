// Pure data — no editor-library imports.
// Consumed by editor.js (Monaco token colors) and hindi-mode.js (tokenizer vocabulary).

export const KEYWORD_MAP = {
  def: "kaam",
  if: "agar",
  elif: "nahi_toh",
  else: "varna",
  for: "dohrayo",
  while: "jabtab",
  in: "mein",
  class: "class",
  try: "koshish",
  except: "siwaye",
  finally: "aant_mein",
  return: "vaapas",
  import: "bharti",
  from: "se",
  as: "jaise",
  pass: "pass",
  break: "ruko",
  continue: "jaari",
  global: "vaishvik",
  nonlocal: "gairsthaniyay",
  lambda: "lambda",
  raise: "uthayo",
  assert: "pushti",
  del: "hatao",
  with: "saath",
  yield: "utpann",
  async: "async",
  await: "prateeksha",
  and: "aur",
  or: "ya",
  not: "nahi",
  is: "hai",
};

export const BUILTIN_MAP = {
  print: "chhapo",
  len: "lambai",
  range: "shreni",
  input: "input",
  int: "purnank",
  float: "dashamlav",
  str: "string",
  bool: "boolean",
  list: "suchi",
  dict: "shabdkosh",
  set: "samuchay",
  tuple: "tapal",
  type: "prakar",
  sum: "yog",
  max: "adhiktam",
  min: "nyuntam",
  abs: "nirapeksh",
  round: "purnankit",
  sorted: "kramabaddh",
  reversed: "ulta",
  enumerate: "ganana",
  zip: "zip",
  map: "map",
  filter: "filter",
  open: "kholo",
  isinstance: "prakar_jaanch",
  super: "super",
  id: "pehchaan",
  hash: "hash",
  next: "agla",
  iter: "punaravartak",
  format: "praroop",
  repr: "ripr",
  ord: "ord",
  chr: "akshar",
  all: "sabhi",
  any: "koi",
  object: "vastu",
};

export const CONSTANT_MAP = { True: "sach", False: "jhooth", None: "kuchhnahi" };

// One-line definitions shown by the hover provider in hindi-mode.js.
// Keyed by the English Python keyword (KEYWORD_MAP's keys).
export const KEYWORD_DOCS = {
  def: "Defines a function.",
  if: "Begins a conditional block; runs its body when the condition is true.",
  elif: "Adds another condition to an if block, checked if prior conditions were false.",
  else: "Runs when no preceding if/elif condition was true.",
  for: "Iterates over a sequence (list, range, string, etc.), running the body once per item.",
  while: "Repeats its body as long as the condition remains true.",
  in: "Tests membership, or introduces the iterable in a for loop.",
  class: "Defines a new class (a blueprint for objects).",
  try: "Begins a block of code that may raise an exception.",
  except: "Catches and handles an exception raised in the try block.",
  finally: "Runs cleanup code that always executes, whether or not an exception occurred.",
  return: "Exits a function, optionally sending back a value.",
  import: "Loads a module so its names can be used.",
  from: "Imports specific names from a module (used with import).",
  as: "Binds an imported module, caught exception, or context manager to a local name.",
  pass: "A no-op placeholder statement — does nothing.",
  break: "Exits the nearest enclosing loop immediately.",
  continue: "Skips to the next iteration of the nearest enclosing loop.",
  global: "Declares that a name refers to a module-level (global) variable.",
  nonlocal: "Declares that a name refers to a variable in an enclosing (non-global) scope.",
  lambda: "Creates a small anonymous function inline.",
  raise: "Triggers an exception.",
  assert: "Raises an AssertionError if the given condition is false.",
  del: "Deletes a name, item, or attribute.",
  with: "Wraps a block in a context manager (e.g. auto-closing a file).",
  yield: "Produces a value from a generator function, pausing execution until resumed.",
  async: "Marks a function as a coroutine, usable with await.",
  await: "Pauses an async function until the awaited coroutine/future completes.",
  and: "Logical AND — true only if both operands are true.",
  or: "Logical OR — true if either operand is true.",
  not: "Logical negation of a boolean value.",
  is: "Tests identity — whether two names refer to the same object.",
};

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
