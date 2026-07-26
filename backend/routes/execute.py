"""Handle /execute/* endpoints. Orchestrates translation restoration and
subprocess execution.

Imports only executor-side core modules — never backend.routes.translate.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.sandbox import run_in_sandbox
from backend.session import session_manager
from core.constants import TRACEBACK_WORD
from core.executor import execute_hindi_source, hindi_to_english_source
from core.output_translator import translate_message, translate_type

router = APIRouter(prefix="/execute", tags=["execute"])


class ExecuteHindiRequest(BaseModel):
    code: str = Field(min_length=1)
    session_id: str


class ExecuteHindiResponse(BaseModel):
    hindi_output: str
    english_output: str
    hindi_error: str
    english_error: str
    success: bool


class ExecuteEnglishRequest(BaseModel):
    code: str = Field(min_length=1)


class ExecuteEnglishResponse(BaseModel):
    output: str
    error: str
    success: bool


def _run_hindi_safely(code: str, reverse_map: dict) -> tuple[str, str]:
    try:
        return execute_hindi_source(code, reverse_map)
    except Exception as exc:
        error_type = type(exc).__name__
        message = str(exc)
        hindi_error = f"{TRACEBACK_WORD}:\n{translate_type(error_type)}"
        if message:
            hindi_error += f": {translate_message(message, reverse_map)}"
        return "", hindi_error


@router.post("/hindi", response_model=ExecuteHindiResponse)
def execute_hindi(request: ExecuteHindiRequest) -> ExecuteHindiResponse:
    session = session_manager.get(request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session_id")

    reverse_map = session.get("reverse_map", {})

    hindi_output, hindi_error = _run_hindi_safely(request.code, reverse_map)

    try:
        english_source = hindi_to_english_source(request.code, reverse_map)
        english_output, english_error = run_in_sandbox(english_source)
    except SyntaxError:
        english_output, english_error = "", hindi_error

    return ExecuteHindiResponse(
        hindi_output=hindi_output,
        english_output=english_output,
        hindi_error=hindi_error,
        english_error=english_error,
        success=hindi_error == "",
    )


@router.post("/english", response_model=ExecuteEnglishResponse)
def execute_english(request: ExecuteEnglishRequest) -> ExecuteEnglishResponse:
    output, error = run_in_sandbox(request.code)
    return ExecuteEnglishResponse(output=output, error=error, success=error == "")
