"""Cloudflare Workers AI provider adapter."""
from __future__ import annotations

import json
import os
from typing import Any

from frontend.models.ai_task_result import AITaskRequest
from frontend.services.ai_providers.base import AIProviderAdapter, ProviderResponse
from frontend.services.ai_providers.http_client import SafeHttpClient, sanitize_text


from frontend.services.ai_providers.local_key_loader import get_provider_secret


class CloudflareProvider(AIProviderAdapter):
    def __init__(self, profile, client: SafeHttpClient | None = None):
        super().__init__(profile)
        self.client = client or SafeHttpClient(timeout=float(getattr(profile, "timeout", 20.0)), retries=1)

    def _api_key(self) -> str:
        return get_provider_secret(self.profile.env_key or "CLOUDFLARE_API_TOKEN")

    def _account_id(self) -> str:
        return get_provider_secret((getattr(self.profile, "extra", {}) or {}).get("account_env_key", "CLOUDFLARE_ACCOUNT_ID"))

    def is_available(self) -> bool:
        return self.profile.enabled and bool(self._api_key()) and bool(self._account_id())

    def generate(self, request: AITaskRequest) -> ProviderResponse:
        token = self._api_key(); account_id = self._account_id()
        if request.privacy_mode == "local_only":
            return ProviderResponse(False, error_type="privacy_blocked", error_message="local_only blocks external providers")
        if not token or not account_id:
            return ProviderResponse(False, error_type="missing_key", error_message="Cloudflare token or account id is not configured")
        base = (self.profile.base_url or "https://api.cloudflare.com/client/v4").rstrip("/")
        url = f"{base}/accounts/{account_id}/ai/run/{self.default_model}"
        payload = {"messages": [{"role": "user", "content": request.prompt}]}
        resp = self.client.post_json(url, payload, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, sensitive_values=[token, account_id])
        if not resp.ok:
            return ProviderResponse(False, error_type=resp.error_type, error_message=sanitize_text(resp.error_message, [token, account_id]), invalid_json=resp.invalid_json)
        data = resp.data if isinstance(resp.data, dict) else {}
        result = data.get("result") if isinstance(data.get("result"), dict) else data
        text = str(result.get("response") or result.get("text") or "").strip()
        parsed = {}
        if request.require_json and text:
            try: parsed = json.loads(text)
            except Exception: parsed = {}
        return ProviderResponse(True, text=text, data=parsed, model=self.default_model)
