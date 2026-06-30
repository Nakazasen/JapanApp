"""AI task request/result contracts for JapanApp."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from frontend.models.ai_provider import AITaskType, ModelTier


@dataclass
class AITaskRequest:
    task_type: AITaskType | str
    prompt: str
    payload: dict[str, Any] = field(default_factory=dict)
    privacy_mode: str = "redacted"
    require_json: bool = True
    critical: bool = False
    preferred_provider: str | None = None


@dataclass
class AITaskResult:
    ok: bool
    content: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    provider_used: str = ""
    provider_tier: int = int(ModelTier.CHEAP_FREE_POOL)
    fallback_used: bool = False
    judge_provider: str = ""
    model: str = ""
    attempts: list[dict[str, Any]] = field(default_factory=list)
    error_type: str = ""
    error_message: str = ""

    def feedback_contract(self) -> dict[str, Any]:
        data = dict(self.data or {})
        return {
            "provider_used": self.provider_used,
            "provider_tier": self.provider_tier,
            "fallback_used": self.fallback_used,
            "judge_provider": self.judge_provider,
            "score_total": int(data.get("score_total", 0)),
            "scores": data.get("scores", {}),
            "critical_errors": data.get("critical_errors", []),
            "unnatural_phrases": data.get("unnatural_phrases", []),
            "better_version": data.get("better_version", ""),
            "vietnamese_explanation": data.get("vietnamese_explanation", ""),
            "next_drill": data.get("next_drill", ""),
            "weakness_tags": data.get("weakness_tags", []),
        }
