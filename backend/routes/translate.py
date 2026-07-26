"""Handle /translate/* endpoints. Calls the Phase 1 core pipeline.

Manages sessions via SessionManager. Imports only translation-side core
modules — never backend.sandbox or anything execution-related.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.session import session_manager
from core.constants import REVERSE_BUILTIN_MAP
from core.executor import hindi_to_english_source
from core.hindi_parser import extract_hindi_identifiers
from core.llm_reverse import reverse_translate_identifiers
from core.main import translate_source

router = APIRouter(prefix="/translate", tags=["translate"])


class ToHindiRequest(BaseModel):
    code: str = Field(min_length=1)
    session_id: str | None = None


class ToHindiResponse(BaseModel):
    hindi_code: str
    session_id: str
    translation_map: dict[str, str]
    error: str = ""


class ToEnglishRequest(BaseModel):
    code: str = Field(min_length=1)
    session_id: str


class ToEnglishResponse(BaseModel):
    english_code: str
    error: str = ""


@router.post("/to-hindi", response_model=ToHindiResponse)
def to_hindi(request: ToHindiRequest) -> ToHindiResponse:
    session_id = request.session_id
    if session_id is None or session_manager.get(session_id) is None:
        session_id = session_manager.create()

    hindi_code, reverse_map = translate_source(request.code, verbose=False)
    translation_map = {
        english: hindi
        for hindi, english in reverse_map.items()
        if hindi not in REVERSE_BUILTIN_MAP
    }

    session_manager.update(
        session_id,
        reverse_map=reverse_map,
        translation_map=translation_map,
        hindi_source=hindi_code,
        english_source=request.code,
    )

    return ToHindiResponse(
        hindi_code=hindi_code,
        session_id=session_id,
        translation_map=translation_map,
        error="",
    )


@router.post("/to-english", response_model=ToEnglishResponse)
def to_english(request: ToEnglishRequest) -> ToEnglishResponse:
    session = session_manager.get(request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session_id")

    reverse_map = session.get("reverse_map")
    if reverse_map is None:
        identifiers = extract_hindi_identifiers(request.code)
        translation_map = reverse_translate_identifiers(identifiers["flat_unique"])
        reverse_map = {**translation_map, **REVERSE_BUILTIN_MAP}

    english_code = hindi_to_english_source(request.code, reverse_map)

    session_manager.update(
        request.session_id, reverse_map=reverse_map, english_source=english_code
    )

    return ToEnglishResponse(english_code=english_code, error="")
