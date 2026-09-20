"""
Thin wrapper around the OpenAI Python SDK so we can point it at:
  - NVIDIA NIM (https://integrate.api.nvidia.com/v1, or a self-hosted NIM container)
  - A self-hosted MatrAIx-Persona-8B server (vLLM / TGI / any OpenAI-compatible server)
  - OpenAI itself, or any other compatible provider

Because all of these speak the same /chat/completions wire format, we never need
provider-specific branches — only base_url / api_key / model change.
"""
from __future__ import annotations
import json
import os
from typing import Optional

from openai import OpenAI

from app.models import ModelSettings


DEFAULT_BASE_URL = os.getenv("AI_BASE_URL", "https://integrate.api.nvidia.com/v1")
DEFAULT_API_KEY = os.getenv("AI_API_KEY", "")
DEFAULT_MODEL = os.getenv("AI_MODEL", "matraix/persona-8b")


def get_client(settings: Optional[ModelSettings] = None) -> tuple[OpenAI, str]:
    """Build an OpenAI client + model name from either per-request settings
    (saved by the user in the Settings modal) or the server's .env defaults."""
    base_url = settings.base_url if settings else DEFAULT_BASE_URL
    api_key = (settings.api_key if settings else DEFAULT_API_KEY) or "not-needed"
    model = settings.model if settings else DEFAULT_MODEL

    client = OpenAI(base_url=base_url, api_key=api_key)
    return client, model


class AIClientError(Exception):
    pass


def chat_json(
    system_prompt: str,
    user_prompt: str,
    settings: Optional[ModelSettings] = None,
    temperature: float = 0.6,
    max_tokens: int = 4096,
) -> dict:
    """Send a chat completion request and parse the reply as JSON.

    MatrAIx-Persona-8B (and most modern OpenAI-compatible servers) support
    `response_format={"type": "json_object"}`. If the endpoint rejects that
    parameter we retry once without it and parse leniently.
    """
    client, model = get_client(settings)

    def _call(with_json_mode: bool):
        kwargs = dict(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        if with_json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        return client.chat.completions.create(**kwargs)

    try:
        completion = _call(with_json_mode=True)
    except Exception:
        completion = _call(with_json_mode=False)

    raw = completion.choices[0].message.content or ""
    return _extract_json(raw)


def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    # Strip ```json ... ``` fences if the model added them anyway
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        # last-ditch: find the first { and last } and try again
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                pass
        raise AIClientError(f"Model did not return valid JSON: {e}\n---\n{raw[:800]}")
