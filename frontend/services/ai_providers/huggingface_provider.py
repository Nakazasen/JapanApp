"""HuggingFace Inference API provider adapter."""
from __future__ import annotations

import json
import os
from typing import Any

from frontend.models.ai_task_result import AITaskRequest
from frontend.services.ai_providers.base import AIProviderAdapter, ProviderResponse
from frontend.services.ai_providers.http_client import SafeHttpClient, sanitize_text


def _extract_text(payload: Any) -> str:
    if isinstance(payload, list) and payload:
        first = payload[0]
        if isinstance(first, dict):
            return str(first.get("generated_text") or first.get("summary_text") or first.get("translation_text") or "").strip()
    if isinstance(payload, dict):
        return str(payload.get("generated_text") or payload.get("text") or ((payload.get("choices") or [{}])[0].get("text") if payload.get("choices") else "") or "").strip()
    return str(payload or "").strip()


from frontend.services.ai_providers.local_key_loader import get_provider_secret


class HuggingFaceProvider(AIProviderAdapter):
    def __init__(self, profile, client: SafeHttpClient | None = None):
        super().__init__(profile)
        self.client = client or SafeHttpClient(timeout=float(getattr(profile, "timeout", 20.0)), retries=1)

    def _api_key(self) -> str:
        return get_provider_secret(self.profile.env_key or "HUGGINGFACE_API_KEY")

    def is_available(self) -> bool:
        return self.profile.enabled and bool(self._api_key())

    def generate(self, request: AITaskRequest) -> ProviderResponse:
        key = self._api_key()
        if request.privacy_mode == "local_only":
            return ProviderResponse(False, error_type="privacy_blocked", error_message="local_only blocks external providers")
        if not key:
            return ProviderResponse(False, error_type="missing_key", error_message="HuggingFace API key is not configured")
        base = (self.profile.base_url or "https://api-inference.huggingface.co/models").rstrip("/")
        url = base if base.endswith(self.default_model) else f"{base}/{self.default_model}"
        payload = {"inputs": request.prompt, "parameters": {"max_new_tokens": 512, "temperature": 0.2}}
        resp = self.client.post_json(url, payload, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, sensitive_values=[key])
        if not resp.ok:
            return ProviderResponse(False, error_type=resp.error_type, error_message=sanitize_text(resp.error_message, [key]), invalid_json=resp.invalid_json)
        text = _extract_text(resp.data)
        parsed = {}
        if request.require_json and text:
            try: parsed = json.loads(text)
            except Exception: parsed = {}
        return ProviderResponse(True, text=text, data=parsed, model=self.default_model)
