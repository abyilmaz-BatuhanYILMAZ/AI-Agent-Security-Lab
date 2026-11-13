"""Minimal model interface and optional OpenAI-compatible inference adapter."""
from __future__ import annotations

import json
import os
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .gateway import Decision


class ModelFailure(RuntimeError):
    """Known inference or response-format failure without exposing provider content."""


class DecisionModel(Protocol):
    def decide(self, messages: list[dict[str, str]]) -> Decision:
        ...


def validate_endpoint(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("inference endpoint must not contain URL credentials")
    if parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.fragment:
        raise ValueError("expected an absolute HTTP(S) inference endpoint")
    if parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("unencrypted inference traffic is limited to literal loopback hosts")
    if not parsed.path or parsed.path == "/":
        raise ValueError("endpoint must include a Chat Completions API path")
    return url


class CompatibleChatModel:
    """Calls only a user-selected inference endpoint. No external tool execution."""

    def __init__(self, model: str, endpoint: str, api_key_env: str = "AI_LAB_API_KEY",
                 timeout: float = 45.0, temperature: float = 0.0):
        if not model.strip() or len(model) > 160:
            raise ValueError("specify a valid model ID")
        if not (0 <= temperature <= 2) or timeout <= 0 or timeout > 300:
            raise ValueError("invalid sampling temperature or timeout")
        self.model = model
        self.endpoint = validate_endpoint(endpoint)
        self.timeout = timeout
        self.temperature = temperature
        self._key = os.environ.get(api_key_env, "")

    def decide(self, messages: list[dict[str, str]]) -> Decision:
        request_data = json.dumps({
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 300,
        }).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._key:
            headers["Authorization"] = "Bearer " + self._key
        request = Request(self.endpoint, request_data, headers, method="POST")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read(256_001)
        except HTTPError as exc:
            raise ModelFailure(f"inference HTTP {exc.code}") from None
        except (URLError, TimeoutError, OSError) as exc:
            raise ModelFailure("inference network or timeout failure") from None
        if len(raw) > 256_000:
            raise ModelFailure("model response exceeded size limit")
        try:
            value = json.loads(raw.decode("utf-8"))
            content = value["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise ValueError("model did not return text content")
            decision = json.loads(content)
            return Decision.from_raw(decision)
        except (KeyError, IndexError, TypeError, ValueError, UnicodeError, json.JSONDecodeError):
            raise ModelFailure("invalid JSON decision from inference model") from None
