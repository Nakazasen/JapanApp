"""OpenAI-compatible provider adapter for Groq/Cerebras/OpenRouter/Mistral/SambaNova/GitHub/AI21."""
from __future__ import annotations

import json
import os
from typing import Any

from frontend.models.ai_task_result import AITaskRequest
from frontend.services.ai_providers.base import AIProviderAdapter, ProviderResponse
from frontend.services.ai_providers.http_client import SafeHttpClient, sanitize_text


def _endpoint(base_url: str) -> str:
    base = (base_url or "").rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def _extract_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if choices:
        message = choices[0].get("message") or {}
        content = message.get("content", "")
        if isinstance(content, list):
            return "".join(str(p.get("text", "")) for p in content if isinstance(p, dict)).strip()
        return str(content or choices[0].get("text", "")).strip()
    return str(payload.get("text") or payload.get("output") or "").strip()


from frontend.services.ai_providers.local_key_loader import get_provider_secret


class OpenAICompatibleProvider(AIProviderAdapter):
    def __init__(self, profile, client: SafeHttpClient | None = None):
        super().__init__(profile)
        self.client = client or SafeHttpClient(timeout=float(getattr(profile, "timeout", 20.0)), retries=1)

    def _api_key(self) -> str:
        return get_provider_secret(self.profile.env_key or "")

    def is_available(self) -> bool:
        return self.profile.enabled and bool(self.profile.base_url) and bool(self.default_model) and bool(self._api_key())

    def generate(self, request: AITaskRequest) -> ProviderResponse:
        api_key = self._api_key()
        if request.privacy_mode == "local_only":
            return ProviderResponse(False, error_type="privacy_blocked", error_message="local_only blocks external providers")
        if not api_key:
            return ProviderResponse(False, error_type="missing_key", error_message=f"{self.provider_id} API key is not configured")
        if not self.profile.base_url:
            return ProviderResponse(False, error_type="provider_error", error_message=f"{self.provider_id} base URL is not configured")

        payload = {
            "model": self.default_model,
            "messages": [
                {"role": "system", "content": "Return concise, valid output for the requested JapanApp language-learning task."},
                {"role": "user", "content": request.prompt},
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "JapanApp-AIResourceLayer/1.0",
        }
        if self.provider_id == "openrouter":
            headers.update({"HTTP-Referer": "http://localhost", "X-Title": "JapanApp"})

        resp = self.client.post_json(_endpoint(self.profile.base_url), payload, headers=headers, timeout=float(getattr(self.profile, "timeout", 20.0)), sensitive_values=[api_key])
        if not resp.ok:
            return ProviderResponse(False, error_type=resp.error_type, error_message=sanitize_text(resp.error_message, [api_key]), invalid_json=resp.invalid_json)
        data = resp.data if isinstance(resp.data, dict) else {"raw": resp.data}
        text = _extract_text(data)
        parsed = {}
        if request.require_json and text:
            try:
                parsed = json.loads(text)
            except Exception:
                parsed = {}
        return ProviderResponse(True, text=text, data=parsed, model=self.default_model)
