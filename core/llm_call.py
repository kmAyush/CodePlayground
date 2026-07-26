"""Send English identifiers to the Sarvam LLM and return a Hindi translation map."""

import json
import os

from dotenv import load_dotenv
from sarvamai import SarvamAI
from sarvamai.core.api_error import ApiError

load_dotenv()

# Falls back to a placeholder so the module (and tests that patch `client`)
# can import without a real key configured; real calls require SARVAM_API.
client = SarvamAI(api_subscription_key=os.getenv("SARVAM_API") or "not-set")

MODEL = "sarvam-30b"

SYSTEM_PROMPT = """You translate Python identifiers from English to Hindi.

Input:  JSON {"identifiers": ["student", "marks", "items", "append"]}
Output: JSON {"student":"छात्र","marks":"अंक","items":"मदें","append":"जोड़ो"}

Rules:
- Translate ALL identifiers, including method names like items, append, split.
- For multi-word snake_case identifiers, translate each part and join with
  underscores: "student_marks" -> "छात्र_अंक".
- Output values must be pure Devanagari — no English letters.
- Respond with JSON only. No markdown fences, no explanation.
"""


def translate_identifiers(flat_unique: list[str]) -> dict[str, str]:
    if not flat_unique:
        return {}

    payload = json.dumps({"identifiers": flat_unique}, ensure_ascii=False)

    try:
        response = client.chat.completions(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": payload},
            ],
            temperature=0.1,
            reasoning_effort=None,
            max_tokens=1024,
        )
    except ApiError as exc:
        if exc.status_code == 429:
            raise RuntimeError(
                f"Rate limit exceeded calling Sarvam API (status {exc.status_code}): {exc.body}"
            ) from exc
        raise RuntimeError(
            f"Sarvam API error (status {exc.status_code}): {exc.body}"
        ) from exc

    choice = response.choices[0]

    if choice.finish_reason == "length":
        raise RuntimeError(
            "Sarvam response truncated (finish_reason=length); reduce batch size and retry"
        )

    content = choice.message.content
    if not content:
        raise RuntimeError("Sarvam response had empty content")

    try:
        translated = json.loads(content)
    except json.JSONDecodeError as exc:
        preview = content[:200]
        raise RuntimeError(f"Sarvam response was not valid JSON: {preview!r}") from exc

    translated = _normalize_translation_shape(translated, flat_unique)

    return {name: translated.get(name, name) for name in flat_unique}


def _normalize_translation_shape(translated: dict, flat_unique: list[str]) -> dict:
    """Recover from the model returning {"identifiers": [...]} (same order as
    the request) instead of the requested {english: hindi} mapping.
    """
    if set(flat_unique) & set(translated.keys()):
        return translated

    values = translated.get("identifiers") if isinstance(translated, dict) else None
    if values is None and len(translated) == 1:
        values = next(iter(translated.values()))

    if isinstance(values, list) and len(values) == len(flat_unique):
        return dict(zip(flat_unique, values))

    return translated
