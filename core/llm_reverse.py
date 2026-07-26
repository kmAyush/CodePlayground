"""Send Hindi identifiers to the Sarvam LLM and return an English translation map."""

import json

from sarvamai.core.api_error import ApiError

from core.llm_call import MODEL, client

SYSTEM_PROMPT = """You translate Python identifiers from Hindi to English.

Input:  JSON {"identifiers": ["jod", "chatr", "ank"]}
Output: JSON {"jod": "add", "chatr": "student", "ank": "marks"}

Rules:
- Output values must be valid Python identifiers: snake_case, no spaces,
  no Devanagari characters.
- Respond with JSON only. No markdown fences, no explanation.
"""


def reverse_translate_identifiers(flat_unique: list[str]) -> dict[str, str]:
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

    return {name: translated.get(name, name) for name in flat_unique}
