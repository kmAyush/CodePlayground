// Typed fetch wrappers for all backend endpoints. Never touches the DOM.

const API_BASE = "http://localhost:8000";

async function post(path, body) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (networkError) {
    throw new Error(`${path}: network error — is the backend running? (${networkError.message})`);
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const data = await response.json();
      detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data);
    } catch {
      // response body wasn't JSON — fall back to statusText
    }
    throw new Error(`${path} failed (${response.status}): ${detail}`);
  }

  return response.json();
}

async function translateToHindi(code, sessionId) {
  const data = await post("/translate/to-hindi", { code, session_id: sessionId ?? null });
  return {
    hindiCode: data.hindi_code,
    sessionId: data.session_id,
    translationMap: data.translation_map,
    error: data.error,
  };
}

async function translateToEnglish(code, sessionId) {
  const data = await post("/translate/to-english", { code, session_id: sessionId });
  return { englishCode: data.english_code, error: data.error };
}

async function executeHindi(code, sessionId) {
  const data = await post("/execute/hindi", { code, session_id: sessionId });
  return {
    hindiOutput: data.hindi_output,
    englishOutput: data.english_output,
    hindiError: data.hindi_error,
    englishError: data.english_error,
    success: data.success,
  };
}

async function executeEnglish(code) {
  const data = await post("/execute/english", { code });
  return { output: data.output, error: data.error, success: data.success };
}

export { API_BASE, translateToHindi, translateToEnglish, executeHindi, executeEnglish };
