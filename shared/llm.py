"""Thin Gemini wrapper with a deterministic mock mode.

Why a mock mode? You can build and test everything offline, with no API key and no cost.
When credentials are present (or LLM_MODE=gemini) real Gemini calls are used.
If a live call fails, we fall back to the mock result and report source="fallback".
"""
import logging
import os
from typing import Callable, Optional, Type, TypeVar

from pydantic import BaseModel

from . import config

log = logging.getLogger("argus.llm")
T = TypeVar("T", bound=BaseModel)
_client = None


def _get_api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip() or config.GEMINI_API_KEY.strip()


def mode() -> str:
    if config.LLM_MODE == "mock":
        return "mock"
    if config.LLM_MODE == "gemini":
        return "gemini"
    return "gemini" if (_get_api_key() or config.USE_VERTEX) else "mock"


def _get_client():
    global _client
    key = _get_api_key()
    if _client is None:
        from google import genai  # imported lazily so mock mode needs no Google packages
        if config.USE_VERTEX:
            _client = genai.Client(vertexai=True, project=config.GCP_PROJECT, location=config.GCP_LOCATION)
        else:
            _client = genai.Client(api_key=key)
    return _client


def generate_json(
    prompt: str,
    schema: Type[T],
    mock: Callable[[], T],
    *,
    system: str = "",
    model: Optional[str] = None,
    temperature: float = 0.1,
) -> tuple[T, str]:
    """Return (parsed_result, source) where source is 'gemini', 'mock' or 'fallback'."""
    if mode() == "mock":
        return mock(), "mock"
    last_err = None
    for _ in range(2):  # one retry
        try:
            from google.genai import types
            resp = _get_client().models.generate_content(
                model=model or config.MODEL_FAST,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system or None,
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=temperature,
                ),
            )
            parsed = getattr(resp, "parsed", None)
            if isinstance(parsed, schema):
                return parsed, "gemini"
            return schema.model_validate_json(resp.text), "gemini"
        except Exception as exc:  # noqa: BLE001
            last_err = exc
    log.warning("Gemini call failed (%s); using fallback", last_err)
    return mock(), "fallback"
