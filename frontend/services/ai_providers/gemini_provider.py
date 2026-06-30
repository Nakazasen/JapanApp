"""Optional Gemini adapter. Gemini is one provider, not the product default."""
from __future__ import annotations
import os
from frontend.models.ai_task_result import AITaskRequest
from frontend.services.ai_providers.base import AIProviderAdapter, ProviderResponse

class GeminiProvider(AIProviderAdapter):
    def is_available(self) -> bool:
        return bool(os.getenv(self.profile.env_key or "GEMINI_API_KEY")) and self.profile.enabled

    def generate(self, request: AITaskRequest) -> ProviderResponse:
        if not self.is_available():
            return ProviderResponse(False, error_type="auth_failure", error_message="Gemini key missing or provider disabled")
        return ProviderResponse(False, error_type="not_configured", error_message="Live Gemini calls are intentionally opt-in in this router foundation")
