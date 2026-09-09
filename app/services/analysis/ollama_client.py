from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OllamaError(RuntimeError):
    """Raised when Ollama is misconfigured or returns an unusable response."""


class OllamaClient:
    """Thin client for the local Ollama HTTP API."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def model(self) -> str:
        model = (self.settings.ollama_model or "").strip()
        if not model:
            raise OllamaError(
                "OLLAMA_MODEL is not set. Pull a model with `ollama pull <name>`, "
                "then set OLLAMA_MODEL in .env to the exact name from `ollama list`."
            )
        return model

    def list_models(self) -> list[str]:
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/tags"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OllamaError(
                f"Cannot reach Ollama at {self.settings.ollama_base_url}: {exc}"
            ) from exc

        models = response.json().get("models", [])
        return [m.get("name", "") for m in models if m.get("name")]

    def generate(self, prompt: str) -> str:
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.2,
            },
        }
        logger.info("Requesting Ollama analysis with model=%s", self.model)
        try:
            with httpx.Client(timeout=self.settings.ollama_timeout_seconds) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OllamaError(f"Ollama generate request failed: {exc}") from exc

        data = response.json()
        text = data.get("response")
        if not text:
            raise OllamaError("Ollama returned an empty response")
        return text


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_json_object(raw: str) -> dict[str, Any]:
    """Best-effort extraction of a JSON object from LLM text."""
    text = raw.strip()
    fence = _JSON_FENCE_RE.search(text)
    if fence:
        text = fence.group(1).strip()

    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        payload = json.loads(text[start : end + 1])
        if isinstance(payload, dict):
            return payload

    raise OllamaError("Could not parse JSON object from LLM response")
