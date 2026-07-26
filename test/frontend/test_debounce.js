// Manual browser test checklist for frontend/editor.js.
// No automated framework — open frontend/index.html (served via
// `uv run uvicorn backend.app:create_app --factory --reload --port 8000`)
// and walk through each item with the Network/Console tabs open.
//
//   [ ] Type in left (Hindi) panel -> right panel updates after 800ms
//   [ ] Type in right (English) panel -> left panel updates after 800ms
//   [ ] Rapid typing in left -> only ONE API call made (debounce working)
//   [ ] syncLock prevents echo: updating right panel does not re-trigger left
//   [ ] Run button disabled during execution
//   [ ] Run button re-enabled after execution completes
//   [ ] Success: both output panels show output
//   [ ] Error: both panels show error in respective language
//   [ ] Hindi error contains पिछलावा, not "Traceback"
//   [ ] Reset clears both editors and both output panels
//   [ ] Dark/light mode toggle works
//   [ ] Page works on mobile viewport (responsive layout)
//   [ ] Noto Sans Devanagari loaded (check Network tab)
//   [ ] No CORS errors in console
//   [ ] session_id persists across multiple runs (check in-memory state)
