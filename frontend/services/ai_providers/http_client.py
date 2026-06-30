"""Secret-safe HTTP helpers for JapanApp live AI provider adapters.

Uses only the Python standard library so provider plumbing does not add runtime
dependencies. The client is intentionally small, mockable, and conservative:
retries are only used for transient timeout/5xx-style failures.
"""
from __future__ import annotations

import json
import re
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret)([=:]\s*)([A-Za-z0-9_\-\.]{6,})"),
    re.compile(r"(?i)(authorization:\s*bearer\s+)([A-Za-z0-9_\-\.]{6,})"),
    re.compile(r"(?i)(key=)([A-Za-z0-9_\-\.]{6,})"),
]
AUTH_HINTS = ("401", "403", "unauthorized", "forbidden", "invalid api key", "authentication")
QUOTA_HINTS = ("429", "quota", "rate limit", "rate_limit", "too many requests", "resource exhausted")
TIMEOUT_HINTS = ("timeout", "timed out")


def sanitize_text(value: Any, sensitive_values: list[str] | None = None) -> str:
    text = str(value or "")
    for secret in sensitive_values or []:
        if secret:
            text = text.replace(secret, "***MASKED***")
            # Also mask accidental short prefixes/suffixes if present near errors.
            if len(secret) >= 8:
                text = text.replace(secret[0:8], "***MASKED***")
                text = text.replace(secret[len(secret)-8:], "***MASKED***")
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(lambda m: f"{m.group(1)}{m.group(2) if len(m.groups()) > 2 else ''}***MASKED***", text)
    return text


def classify_provider_error(message: Any, status_code: int | None = None) -> str:
    low = f"{status_code or ''} {message}".lower()
    if any(h in low for h in AUTH_HINTS):
        return "auth_failure"
    if any(h in low for h in QUOTA_HINTS):
        return "quota_exhausted"
    if any(h in low for h in TIMEOUT_HINTS):
        return "timeout"
    if "invalid_json" in low or "invalid json" in low:
        return "invalid_json"
    return "provider_error"


@dataclass
class SafeHttpResponse:
    ok: bool
    status_code: int = 0
    data: dict[str, Any] | list[Any] | None = None
    text: str = ""
    error_type: str = ""
    error_message: str = ""
    invalid_json: bool = False
    attempts: int = 1
    headers: dict[str, str] = field(default_factory=dict)


class SafeHttpClient:
    def __init__(self, timeout: float = 20.0, retries: int = 1, opener: Callable[..., Any] | None = None):
        self.timeout = float(timeout)
        self.retries = max(0, int(retries))
        self._opener = opener or urllib.request.urlopen

    def post_json(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        sensitive_values: list[str] | None = None,
    ) -> SafeHttpResponse:
        headers = dict(headers or {})
        headers.setdefault("Content-Type", "application/json")
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        max_attempts = self.retries + 1
        last_error = SafeHttpResponse(False, error_type="provider_error", error_message="Provider request failed")

        for attempt in range(1, max_attempts + 1):
            request = urllib.request.Request(url, data=body, headers=headers, method="POST")
            try:
                with self._opener(request, timeout=timeout or self.timeout) as response:
                    raw = response.read().decode("utf-8")
                    status = int(getattr(response, "status", 200) or 200)
                    try:
                        data = json.loads(raw) if raw else {}
                    except Exception:
                        return SafeHttpResponse(False, status, text=sanitize_text(raw, sensitive_values), error_type="invalid_json", error_message="Provider returned invalid JSON", invalid_json=True, attempts=attempt)
                    return SafeHttpResponse(True, status, data=data, text=raw, attempts=attempt)
            except urllib.error.HTTPError as exc:
                raw = ""
                try:
                    raw = exc.read().decode("utf-8")
                except Exception:
                    raw = str(exc)
                error_type = classify_provider_error(raw or str(exc), exc.code)
                last_error = SafeHttpResponse(False, int(exc.code), text=sanitize_text(raw, sensitive_values), error_type=error_type, error_message=sanitize_text(raw or str(exc), sensitive_values), attempts=attempt)
                if error_type in {"auth_failure", "quota_exhausted"} or attempt >= max_attempts:
                    return last_error
            except (TimeoutError, socket.timeout) as exc:
                last_error = SafeHttpResponse(False, error_type="timeout", error_message=sanitize_text(str(exc) or "Provider request timed out", sensitive_values), attempts=attempt)
                if attempt >= max_attempts:
                    return last_error
            except Exception as exc:
                error_type = classify_provider_error(exc)
                last_error = SafeHttpResponse(False, error_type=error_type, error_message=sanitize_text(exc, sensitive_values), attempts=attempt)
                if error_type != "provider_error" or attempt >= max_attempts:
                    return last_error
            time.sleep(min(0.25 * attempt, 1.0))
        return last_error
