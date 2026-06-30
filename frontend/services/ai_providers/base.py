"""Provider adapter interfaces for JapanApp AI Resource Layer."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from frontend.models.ai_provider import ProviderProfile
from frontend.models.ai_task_result import AITaskRequest

@dataclass
class ProviderResponse:
    ok: bool
    text: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    model: str = ""
    error_type: str = ""
    error_message: str = ""
    invalid_json: bool = False

class AIProviderAdapter:
    def __init__(self, profile: ProviderProfile):
        self.profile = profile
        self.provider_id = profile.provider_id
        self.default_model = profile.default_model

    def is_available(self) -> bool:
        return self.profile.enabled

    def generate(self, request: AITaskRequest) -> ProviderResponse:
        raise NotImplementedError
