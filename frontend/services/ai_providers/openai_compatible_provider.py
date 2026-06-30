"""OpenAI-compatible provider shell for Groq/Cerebras/OpenRouter/Mistral/SambaNova/GitHub/AI21."""
from __future__ import annotations
import os
from frontend.models.ai_task_result import AITaskRequest
from frontend.services.ai_providers.base import AIProviderAdapter, ProviderResponse

class OpenAICompatibleProvider(AIProviderAdapter):
    def is_available(self) -> bool:
        return self.profile.enabled and bool(os.getenv(self.profile.env_key))

    def generate(self, request: AITaskRequest) -> ProviderResponse:
        if not self.is_available():
            return ProviderResponse(False, error_type="auth_failure", error_message=f"{self.provider_id} key missing or disabled")
        return ProviderResponse(False, error_type="not_configured", error_message="OpenAI-compatible live calls are disabled until endpoint/client wiring is enabled")
