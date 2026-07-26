// Panel setup, Monaco editor instances, debounce, sync, run/reset buttons.
// window.monaco is guaranteed populated before this module loads
// (index.html's require() callback calls import("./editor.js") only after
// vs/editor/editor.main has fully resolved).

import { registerHindiLanguage, HINDI_LANG_ID } from "./hindi-mode.js";
import { resolveCssVar, ENGLISH_BUILTINS } from "./theme.js";
import { translateToHindi, translateToEnglish, executeHindi, executeEnglish } from "./api.js";

const monaco = window.monaco;
const DEBOUNCE_MS = 800;

const DEFAULT_ENGLISH = `def greet(name):
    message = "Hello, " + name
    print(message)


for name in ["Asha", "Ravi"]:
    greet(name)
`;

// ---- DOM refs -----------------------------------------------------------
const runBtn            = document.getElementById("run-btn");
const resetBtn          = document.getElementById("reset-btn");
const syncBtn           = document.getElementById("sync-btn");
const themeToggle       = document.getElementById("theme-toggle");
const statusIndicator   = document.getElementById("status-indicator");
const hindiOutputPanel  = document.getElementById("hindi-output");
const englishOutputPanel= document.getElementById("english-output");
const hindiErrorPanel   = document.getElementById("hindi-error");
const englishErrorPanel = document.getElementById("english-error");
const hindiErrorWrap    = document.getElementById("hindi-error-wrap");
const englishErrorWrap  = document.getElementById("english-error-wrap");

// ---- module state -------------------------------------------------------
let sessionId       = null;
let syncLock        = false;
let debounceTimer   = null;
let lastEditedPanel = "english";
let currentTheme    = "light"; // track so we can rebuild Monaco theme on toggle

// ---- status pill --------------------------------------------------------
function setStatus(state, message) {
  statusIndicator.dataset.state = state;
  statusIndicator.textContent = message ??
    { ready: "Ready", busy: "Syncing…", running: "Running…", error: "Error" }[state];
}
function reportError(err) {
  console.error(err);
  setStatus("error", `Error: ${err.message}`);
}

// ---- Monaco theme -------------------------------------------------------
// Monaco themes need explicit hex/rgb values — CSS variables don't work
// inside defineTheme(). We resolve them from the document at theme-apply
// time so style.css remains the single source of truth for colors.
function buildMonacoTheme(variant) {
  // variant: "light" | "dark"
  const c = (name) => resolveCssVar(name) || "#888888";
  return {
    base: variant === "dark" ? "vs-dark" : "vs",
    inherit: true, // inherit base token rules, then override below
    rules: [
      { token: "keyword",   foreground: c("--cm-keyword").replace("#",""),   fontStyle: "bold" },
      { token: "builtin",   foreground: c("--cm-builtin").replace("#","")   },
      { token: "constant",  foreground: c("--cm-constant").replace("#","")  },
      { token: "string",    foreground: c("--cm-string").replace("#","")    },
      { token: "number",    foreground: c("--cm-number").replace("#","")    },
      { token: "comment",   foreground: c("--cm-comment").replace("#",""),   fontStyle: "italic" },
      { token: "decorator", foreground: c("--cm-decorator").replace("#",""), fontStyle: "italic" },
      { token: "operator",  foreground: c("--cm-operator").replace("#","")  },
      { token: "delimiter", foreground: c("--cm-punctuation").replace("#","")},
      { token: "identifier",foreground: c("--cm-variable").replace("#","")  },
      // English panel — Monaco's built-in Python token names
      { token: "keyword.python",          foreground: c("--cm-keyword").replace("#",""),  fontStyle: "bold" },
      { token: "string.python",           foreground: c("--cm-string").replace("#","")   },
      { token: "number.python",           foreground: c("--cm-number").replace("#","")   },
      { token: "comment.python",          foreground: c("--cm-comment").replace("#",""),  fontStyle: "italic" },
      { token: "type.identifier.python",  foreground: c("--cm-class").replace("#","")    },
      { token: "entity.name.function",    foreground: c("--cm-function").replace("#","") },
    ],
    colors: {
      "editor.background":           c("--surface"),
      "editor.foreground":           c("--text"),
      "editorLineNumber.foreground": c("--text-muted"),
      "editor.lineHighlightBackground": variant === "dark" ? "#ffffff0a" : "#0000000a",
      "editorCursor.foreground":     c("--accent"),
      "editor.selectionBackground":  variant === "dark" ? "#6d8bff33" : "#4f6df533",
      "editorBracketMatch.background": variant === "dark" ? "#6d8bff22" : "#4f6df522",
      "editorBracketMatch.border":   c("--accent"),
    },
  };
}

function applyMonacoTheme(variant) {
  monaco.editor.defineTheme("playground-theme", buildMonacoTheme(variant));
  monaco.editor.setTheme("playground-theme");
}

// ---- shared editor options ----------------------------------------------
function sharedOptions(language, fontFamily) {
  return {
    language,
    theme: "playground-theme",
    fontFamily,
    fontSize: 14,
    lineHeight: 22,
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    wordWrap: "on",
    automaticLayout: true,   // resizes with the container — no ResizeObserver needed
    tabSize: 4,
    insertSpaces: true,
    lineNumbers: "on",
    folding: false,           // keep it simple for a playground
    renderLineHighlight: "line",
    bracketPairColorization: { enabled: false }, // we color brackets ourselves
    overviewRulerLanes: 0,
    scrollbar: { verticalScrollbarSize: 6, horizontalScrollbarSize: 6 },
  };
}

// ---- register Hindi language + define initial theme ---------------------
registerHindiLanguage();
// Theme must exist before editors are created; applyTheme() below calls this
// again after CSS vars are set by applyTheme().
applyMonacoTheme("light");

// ---- create editors -----------------------------------------------------
const englishEditor = monaco.editor.create(
  document.getElementById("english-editor"),
  { ...sharedOptions("python", '"JetBrains Mono", "Courier New", monospace'), value: DEFAULT_ENGLISH }
);

const hindiEditor = monaco.editor.create(
  document.getElementById("hindi-editor"),
  { ...sharedOptions(HINDI_LANG_ID, '"Noto Sans Devanagari", monospace'), value: "" }
);

// ---- getters / setters --------------------------------------------------
const getEnglishCode = () => englishEditor.getValue();
const getHindiCode   = () => hindiEditor.getValue();

function setEnglishCode(code) {
  syncLock = true;
  englishEditor.setValue(code);
  syncLock = false;
}
function setHindiCode(code) {
  syncLock = true;
  hindiEditor.setValue(code);
  syncLock = false;
}

// ---- change listeners ---------------------------------------------------
englishEditor.onDidChangeModelContent(() => {
  if (!syncLock) { lastEditedPanel = "english"; scheduleSync(syncToHindi); }
});
hindiEditor.onDidChangeModelContent(() => {
  if (!syncLock) { lastEditedPanel = "hindi"; scheduleSync(syncToEnglish); }
});

// ---- sync logic ---------------------------------------------------------
async function syncToHindi() {
  const code = getEnglishCode();
  if (!code.trim()) return;
  setStatus("busy");
  try {
    const result = await translateToHindi(code, sessionId);
    sessionId = result.sessionId;
    setHindiCode(result.hindiCode);
    setStatus("ready");
  } catch (err) { reportError(err); }
}

async function syncToEnglish() {
  const code = getHindiCode();
  if (!code.trim()) return;
  setStatus("busy");
  try {
    const result = await translateToEnglish(code, sessionId);
    setEnglishCode(result.englishCode);
    setStatus("ready");
  } catch (err) {
    if (!sessionId) {
      try {
        await syncToHindi();
        const retry = await translateToEnglish(code, sessionId);
        setEnglishCode(retry.englishCode);
        setStatus("ready");
        return;
      } catch (retryErr) { reportError(retryErr); return; }
    }
    reportError(err);
  }
}

function scheduleSync(fn) {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(fn, DEBOUNCE_MS);
}

// ---- run / reset / sync buttons -----------------------------------------
function setErrorPanel(wrap, panel, errorText, emptyText) {
  const hasError = Boolean(errorText);
  panel.textContent = hasError ? errorText : emptyText;
  wrap.classList.toggle("has-error", hasError);
}

async function runCode() {
  runBtn.disabled = true;
  runBtn.classList.add("is-busy");
  setStatus("running");
  try {
    if (sessionId) {
      const result = await executeHindi(getHindiCode(), sessionId);
      englishOutputPanel.textContent = result.englishOutput;
      hindiOutputPanel.textContent   = result.hindiOutput;
      setErrorPanel(englishErrorWrap, englishErrorPanel, result.englishError, "No errors");
      setErrorPanel(hindiErrorWrap,   hindiErrorPanel,   result.hindiError,   "कोई त्रुटि नहीं");
    } else {
      const r = await executeEnglish(getEnglishCode());
      englishOutputPanel.textContent = r.output;
      setErrorPanel(englishErrorWrap, englishErrorPanel, r.error, "No errors");
      hindiOutputPanel.textContent = "(हिंदी पैनल खाली है — पहले टाइप करें)";
      setErrorPanel(hindiErrorWrap, hindiErrorPanel, "", "कोई त्रुटि नहीं");
    }
    setStatus("ready");
  } catch (err) { reportError(err); }
  finally {
    runBtn.disabled = false;
    runBtn.classList.remove("is-busy");
  }
}

function resetAll() {
  clearTimeout(debounceTimer);
  sessionId = null;
  syncLock  = false;
  lastEditedPanel = "english";
  setEnglishCode(DEFAULT_ENGLISH);
  setHindiCode("");
  hindiOutputPanel.textContent  = "";
  englishOutputPanel.textContent = "";
  setErrorPanel(englishErrorWrap, englishErrorPanel, "", "No errors");
  setErrorPanel(hindiErrorWrap,   hindiErrorPanel,   "", "कोई त्रुटि नहीं");
  setStatus("ready");
}

function forceSyncNow() {
  clearTimeout(debounceTimer);
  lastEditedPanel === "hindi" ? syncToEnglish() : syncToHindi();
}

runBtn.addEventListener("click",   runCode);
resetBtn.addEventListener("click", resetAll);
syncBtn.addEventListener("click",  forceSyncNow);

// ---- theme toggle -------------------------------------------------------
function applyTheme(theme) {
  currentTheme = theme;
  document.documentElement.dataset.theme = theme;
  themeToggle.textContent = theme === "dark" ? "☀ Light" : "🌙 Dark";
  // CSS vars are now updated — rebuild Monaco theme so colors reflect them.
  applyMonacoTheme(theme);
}

themeToggle.addEventListener("click", () => {
  applyTheme(currentTheme === "dark" ? "light" : "dark");
});

const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
applyTheme(prefersDark ? "dark" : "light");

// ---- bootstrap ----------------------------------------------------------
syncToHindi();
