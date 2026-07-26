// Panel setup, debounce logic, sync lock, run button, output display.
// Imports from api.js only — never talks to the backend directly.
//
// All CM6 imports use bare specifiers — the importmap in index.html routes
// them to pinned esm.sh URLs so every file in this page shares exactly one
// module instance per package. Never mix bare specifiers with full esm.sh
// URLs in the same page; the browser treats different URL strings as
// different module identities even when the content is identical.

import { EditorState } from "@codemirror/state";
import {
  EditorView,
  keymap,
  lineNumbers,
  highlightActiveLine,
  highlightActiveLineGutter,
} from "@codemirror/view";
import {
  defaultKeymap,
  history,
  historyKeymap,
  indentWithTab,
} from "@codemirror/commands";
import {
  indentOnInput,
  indentUnit,
  bracketMatching,
  syntaxHighlighting,
} from "@codemirror/language";
import { python } from "@codemirror/lang-python";

import { hindiSupport } from "./hindi-mode.js";
import { pythonHighlightStyle, highlightBuiltins, ENGLISH_BUILTINS } from "./theme.js";
import { translateToHindi, translateToEnglish, executeHindi, executeEnglish } from "./api.js";

const DEBOUNCE_MS = 800;

const DEFAULT_ENGLISH = `def greet(name):
    message = "Hello, " + name
    print(message)


for name in ["Asha", "Ravi"]:
    greet(name)
`;

// ---- module state -----------------------------------------------------
let sessionId = null;
let syncLock = false;
let debounceTimer = null;
let lastEditedPanel = "english"; // "hindi" | "english" — drives the Sync button

// ---- DOM refs -----------------------------------------------------------
const hindiMount = document.getElementById("hindi-editor");
const englishMount = document.getElementById("english-editor");
const runBtn = document.getElementById("run-btn");
const resetBtn = document.getElementById("reset-btn");
const syncBtn = document.getElementById("sync-btn");
const themeToggle = document.getElementById("theme-toggle");
const statusIndicator = document.getElementById("status-indicator");
const hindiOutputPanel = document.getElementById("hindi-output");
const englishOutputPanel = document.getElementById("english-output");
const hindiErrorPanel = document.getElementById("hindi-error");
const englishErrorPanel = document.getElementById("english-error");
const hindiErrorWrap = document.getElementById("hindi-error-wrap");
const englishErrorWrap = document.getElementById("english-error-wrap");

// ---- status pill --------------------------------------------------------
function setStatus(state, message) {
  statusIndicator.dataset.state = state;
  statusIndicator.textContent = message ?? { ready: "Ready", busy: "Syncing…", running: "Running…", error: "Error" }[state];
}

function reportError(err) {
  console.error(err);
  setStatus("error", `Error: ${err.message}`);
}

// ---- CodeMirror setup -----------------------------------------------------
function makeUpdateListener(onDirty) {
  return EditorView.updateListener.of((update) => {
    if (update.docChanged && !syncLock) onDirty();
  });
}

const sharedExtensions = [
  lineNumbers(),
  highlightActiveLine(),
  highlightActiveLineGutter(),
  history(),
  indentOnInput(),
  indentUnit.of("    "),
  bracketMatching(),
  keymap.of([...defaultKeymap, ...historyKeymap, indentWithTab]),
  EditorView.lineWrapping,
];

const hindiView = new EditorView({
  state: EditorState.create({
    doc: "",
    extensions: [
      ...sharedExtensions,
      ...hindiSupport(),
      makeUpdateListener(onHindiEdited),
    ],
  }),
  parent: hindiMount,
});

const englishView = new EditorView({
  state: EditorState.create({
    doc: DEFAULT_ENGLISH,
    extensions: [
      ...sharedExtensions,
      python(),
      // No { fallback: true } — python() installs defaultHighlightStyle which
      // would suppress a fallback style. We want pythonHighlightStyle to always
      // win and apply our CSS-variable-based colors.
      syntaxHighlighting(pythonHighlightStyle),
      highlightBuiltins(ENGLISH_BUILTINS),
      makeUpdateListener(onEnglishEdited),
    ],
  }),
  parent: englishMount,
});

function getHindiCode() {
  return hindiView.state.doc.toString();
}

function getEnglishCode() {
  return englishView.state.doc.toString();
}

function setHindiCode(code) {
  syncLock = true;
  hindiView.dispatch({ changes: { from: 0, to: hindiView.state.doc.length, insert: code } });
  syncLock = false;
}

function setEnglishCode(code) {
  syncLock = true;
  englishView.dispatch({ changes: { from: 0, to: englishView.state.doc.length, insert: code } });
  syncLock = false;
}

// ---- sync logic -----------------------------------------------------------
async function syncToHindi() {
  const code = getEnglishCode();
  if (!code.trim()) return;
  setStatus("busy");
  try {
    const result = await translateToHindi(code, sessionId);
    sessionId = result.sessionId;
    setHindiCode(result.hindiCode);
    setStatus("ready");
  } catch (err) {
    reportError(err);
  }
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
      } catch (retryErr) {
        reportError(retryErr);
        return;
      }
    }
    reportError(err);
  }
}

function scheduleSync(fn) {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(fn, DEBOUNCE_MS);
}

function onHindiEdited() {
  lastEditedPanel = "hindi";
  scheduleSync(syncToEnglish);
}

function onEnglishEdited() {
  lastEditedPanel = "english";
  scheduleSync(syncToHindi);
}

// ---- run / reset / sync buttons -------------------------------------------
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
      hindiOutputPanel.textContent = result.hindiOutput;
      setErrorPanel(englishErrorWrap, englishErrorPanel, result.englishError, "No errors");
      setErrorPanel(hindiErrorWrap, hindiErrorPanel, result.hindiError, "कोई त्रुटि नहीं");
    } else {
      const englishResult = await executeEnglish(getEnglishCode());
      englishOutputPanel.textContent = englishResult.output;
      setErrorPanel(englishErrorWrap, englishErrorPanel, englishResult.error, "No errors");
      hindiOutputPanel.textContent = "(हिंदी पैनल खाली है — पहले टाइप करें)";
      setErrorPanel(hindiErrorWrap, hindiErrorPanel, "", "कोई त्रुटि नहीं");
    }
    setStatus("ready");
  } catch (err) {
    reportError(err);
  } finally {
    runBtn.disabled = false;
    runBtn.classList.remove("is-busy");
  }
}

function resetAll() {
  clearTimeout(debounceTimer);
  sessionId = null;
  syncLock = false;
  lastEditedPanel = "english";
  setEnglishCode(DEFAULT_ENGLISH);
  setHindiCode("");
  hindiOutputPanel.textContent = "";
  englishOutputPanel.textContent = "";
  setErrorPanel(englishErrorWrap, englishErrorPanel, "", "No errors");
  setErrorPanel(hindiErrorWrap, hindiErrorPanel, "", "कोई त्रुटि नहीं");
  setStatus("ready");
}

function forceSyncNow() {
  clearTimeout(debounceTimer);
  if (lastEditedPanel === "hindi") {
    syncToEnglish();
  } else {
    syncToHindi();
  }
}

runBtn.addEventListener("click", runCode);
resetBtn.addEventListener("click", resetAll);
syncBtn.addEventListener("click", forceSyncNow);

// ---- theme toggle -----------------------------------------------------
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  themeToggle.textContent = theme === "dark" ? "☀ Light" : "🌙 Dark";
}

themeToggle.addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  applyTheme(next);
});

const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
applyTheme(prefersDark ? "dark" : "light");

// ---- initial bootstrap -----------------------------------------------------
syncToHindi();
