"""Gemini REST provider adapter. Gemini is one provider, not the product default."""
from __future__ import annotations

import json
import os
from typing import Any

from frontend.models.ai_task_result import AITaskRequest
from frontend.services.ai_providers.base import AIProviderAdapter, ProviderResponse
from frontend.services.ai_providers.http_client import SafeHttpClient, sanitize_text


from frontend.services.ai_providers.local_key_loader import get_provider_secret

def _extract_text(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        return ""
    parts = ((candidates[0].get("content") or {}).get("parts") or [])
    return "".join(str(p.get("text", "")) for p in parts if isinstance(p, dict)).strip()


class GeminiProvider(AIProviderAdapter):
    def __init__(self, profile, client: SafeHttpClient | None = None):
        super().__init__(profile)
        self.client = client or SafeHttpClient(timeout=float(getattr(profile, "timeout", 20.0)), retries=1)

    def _api_key(self) -> str:
        return get_provider_secret(self.profile.env_key or "GEMINI_API_KEY")

    def is_available(self) -> bool:
        return self.profile.enabled and bool(self._api_key())

    def generate(self, request: AITaskRequest) -> ProviderResponse:
        api_key = self._api_key()
        if request.privacy_mode == "local_only":
            return ProviderResponse(False, error_type="privacy_blocked", error_message="local_only blocks external providers")
        if not api_key:
            return ProviderResponse(False, error_type="missing_key", error_message="Gemini API key is not configured")
        model = self.default_model or "gemini-2.5-flash"
        base = (self.profile.base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        url = f"{base}/models/{model}:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": request.prompt}]}], "generationConfig": {"temperature": 0.2}}
        resp = self.client.post_json(url, payload, headers={"Content-Type": "application/json"}, timeout=float(getattr(self.profile, "timeout", 20.0)), sensitive_values=[api_key])
        if not resp.ok:
            return ProviderResponse(False, error_type=resp.error_type, error_message=sanitize_text(resp.error_message, [api_key]), invalid_json=resp.invalid_json)
        data = resp.data if isinstance(resp.data, dict) else {}
        text = _extract_text(data)
        parsed: dict[str, Any] = {}
        if request.require_json and text:
            try:
                parsed = json.loads(text)
            except Exception:
                parsed = {}
        return ProviderResponse(True, text=text, data=parsed, model=model)
